"""Main pipeline orchestrating the full podcast generation process."""
import logging
import tempfile
from pathlib import Path

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn

from .extract.url import extract_from_url
from .extract.pdf import extract_from_pdf
from .extract.text import extract_from_text, strip_markdown, read_stdin, truncate_content
from .script.generator import generate_script, save_script, load_script
from .tts.elevenlabs import ElevenLabsTTS, DEFAULT_VOICES as ELEVEN_VOICES
from .tts.edge import EdgeTTS, DEFAULT_VOICES as EDGE_VOICES
from .tts.openai import OpenAITTS, DEFAULT_VOICES as OPENAI_VOICES
from .audio.mixer import mix_podcast
from .audio.effects import get_audio_duration
from .output.metadata import apply_id3_tags, save_episode_metadata
from .output.transcript import generate_srt, generate_text_transcript

logger = logging.getLogger(__name__)
console = Console()


def _get_tts_backend(backend_name: str):
    """Get a TTS backend instance by name.

    Args:
        backend_name: One of 'elevenlabs', 'edge', 'openai'.

    Returns:
        TTSBackend instance.
    """
    if backend_name == "elevenlabs":
        return ElevenLabsTTS()
    elif backend_name == "edge":
        return EdgeTTS()
    elif backend_name == "openai":
        return OpenAITTS()
    else:
        raise ValueError(f"Unknown TTS backend: {backend_name}. Use 'elevenlabs', 'edge', or 'openai'.")


def _get_default_voices(backend_name: str) -> dict:
    """Get default voice mapping for a backend."""
    if backend_name == "elevenlabs":
        return ELEVEN_VOICES
    elif backend_name == "edge":
        return EDGE_VOICES
    elif backend_name == "openai":
        return OPENAI_VOICES
    return EDGE_VOICES


def _resolve_voice(speaker: str, voice_map: dict, defaults: dict) -> str:
    """Resolve voice for a speaker.

    Args:
        speaker: Speaker name/role.
        voice_map: User-provided voice mapping.
        defaults: Default voices for the backend.

    Returns:
        Voice identifier string.
    """
    # Check user-specified mapping first
    if speaker in voice_map:
        return voice_map[speaker]
    # Check defaults
    if speaker in defaults:
        return defaults[speaker]
    # Fall back to first default voice
    return list(defaults.values())[0]


def extract_content(
    topic: str | None = None,
    url: str | None = None,
    file_path: str | None = None,
    from_stdin: bool = False,
) -> tuple[str, str]:
    """Extract content from the input source.

    Args:
        topic: Topic string.
        url: URL to extract from.
        file_path: File path to extract from.
        from_stdin: Read from stdin.

    Returns:
        Tuple of (content_text, source_type).
    """
    if url:
        content = extract_from_url(url)
        return truncate_content(content), "url"
    elif file_path:
        path = Path(file_path)
        if path.suffix.lower() == ".pdf":
            content = extract_from_pdf(file_path)
            return truncate_content(content), "pdf"
        else:
            content = extract_from_text(file_path)
            if path.suffix.lower() == ".md":
                content = strip_markdown(content)
            return truncate_content(content), "file"
    elif from_stdin:
        content = read_stdin()
        return truncate_content(content), "stdin"
    elif topic:
        return topic, "topic"
    else:
        raise ValueError("No input provided. Specify a topic, --url, --file, or pipe to stdin.")


def run_pipeline(
    topic: str | None = None,
    url: str | None = None,
    file_path: str | None = None,
    from_stdin: bool = False,
    from_script: str | None = None,
    script_only: bool = False,
    output: str = "episode.mp3",
    speakers: int = 2,
    style: str = "casual",
    length: int = 10,
    tts_backend: str = "edge",
    voice_map: dict | None = None,
    model: str = "claude-sonnet-4-20250514",
) -> str:
    """Run the full podcast generation pipeline.

    Args:
        topic: Topic string to discuss.
        url: URL to extract content from.
        file_path: File to extract content from.
        from_stdin: Read content from stdin.
        from_script: Path to existing YAML script to resume from.
        script_only: Only generate the script, don't create audio.
        output: Output MP3 file path.
        speakers: Number of speakers.
        style: Podcast style.
        length: Target length in minutes.
        tts_backend: TTS backend to use.
        voice_map: Custom voice mapping {speaker: voice_name}.
        model: LLM model to use.

    Returns:
        Path to the output file (MP3 or YAML if script_only).
    """
    if voice_map is None:
        voice_map = {}

    output_dir = str(Path(output).parent or ".")
    output_stem = Path(output).stem

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TimeElapsedColumn(),
        console=console,
    ) as progress:

        # === STAGE 1 & 2: Extract content (skip if resuming from script) ===
        if from_script:
            task = progress.add_task("[cyan]Loading script...", total=1)
            script = load_script(from_script)
            progress.update(task, completed=1)
            console.print(f"[green]\u2713[/green] Loaded script from {from_script} ({len(script)} entries)")
            source_type = "script"
        else:
            task = progress.add_task("[cyan]Extracting content...", total=1)
            content, source_type = extract_content(
                topic=topic, url=url, file_path=file_path, from_stdin=from_stdin,
            )
            progress.update(task, completed=1)
            console.print(f"[green]\u2713[/green] Extracted {len(content)} chars from {source_type}")

            # === STAGE 3: Generate script ===
            task = progress.add_task("[cyan]Generating podcast script...", total=1)
            script = generate_script(
                content=content,
                style=style,
                length_minutes=length,
                speakers=speakers,
                model=model,
            )
            progress.update(task, completed=1)

            speech_count = sum(1 for e in script if "speaker" in e)
            sfx_count = sum(1 for e in script if "sfx" in e)
            console.print(
                f"[green]\u2713[/green] Generated script: {speech_count} lines, {sfx_count} effects"
            )

        # If script-only mode, save and return
        if script_only:
            script_path = output if output.endswith((".yaml", ".yml")) else f"{output_stem}_script.yaml"
            save_script(script, script_path)
            console.print(f"[green]\u2713[/green] Script saved to {script_path}")
            return script_path

        # === STAGE 4: TTS ===
        tts = _get_tts_backend(tts_backend)
        defaults = _get_default_voices(tts_backend)

        speech_entries = [e for e in script if "speaker" in e]
        task = progress.add_task(
            f"[cyan]Synthesizing speech ({tts.name})...",
            total=len(speech_entries),
        )

        work_dir = tempfile.mkdtemp(prefix="podforge_")
        segments = []
        speech_idx = 0

        for entry in script:
            if "sfx" in entry:
                segments.append({"type": "sfx", "audio_path": ""})
                continue

            speaker = entry["speaker"]
            text = entry["text"]
            voice = _resolve_voice(speaker, voice_map, defaults)

            audio_path = str(Path(work_dir) / f"speech_{speech_idx:04d}.mp3")

            try:
                tts.synthesize(text, voice, audio_path)
            except Exception as e:
                logger.error(f"TTS failed for segment {speech_idx}: {e}")
                raise RuntimeError(
                    f"TTS synthesis failed for segment {speech_idx} "
                    f"(speaker={speaker}): {e}"
                ) from e

            segments.append({
                "type": "speech",
                "audio_path": audio_path,
                "speaker": speaker,
            })

            speech_idx += 1
            progress.update(task, advance=1)

        console.print(f"[green]\u2713[/green] Synthesized {speech_idx} speech segments")

        # === STAGE 5: Mix ===
        task = progress.add_task("[cyan]Mixing podcast...", total=1)

        mix_podcast(
            speech_segments=segments,
            output_path=output,
            work_dir=str(Path(work_dir) / "mix"),
        )

        progress.update(task, completed=1)
        duration = get_audio_duration(output)
        console.print(f"[green]\u2713[/green] Mixed podcast: {duration:.0f}s")

        # === STAGE 6: Output ===
        task = progress.add_task("[cyan]Finalizing output...", total=1)

        # Determine title
        if topic:
            title = topic[:80]
        elif url:
            title = f"Discussion: {url[:60]}"
        elif file_path:
            title = f"Discussion: {Path(file_path).stem}"
        else:
            title = "Podcast Episode"

        # Apply ID3 tags
        apply_id3_tags(
            mp3_path=output,
            title=title,
            description=f"Generated by PodForge | Style: {style} | Speakers: {speakers}",
        )

        # Get segment durations for transcript
        segment_durations = []
        for seg in segments:
            if seg["type"] == "speech":
                try:
                    dur = get_audio_duration(seg["audio_path"])
                    segment_durations.append(dur)
                except Exception:
                    segment_durations.append(3.0)  # Estimate

        # Generate transcript files
        srt_path = str(Path(output_dir) / f"{output_stem}.srt")
        generate_srt(script, segment_durations, srt_path)

        txt_path = str(Path(output_dir) / f"{output_stem}_transcript.txt")
        generate_text_transcript(script, txt_path, title=title)

        # Get unique speakers from the script
        speaker_names = list(dict.fromkeys(
            e["speaker"] for e in script if "speaker" in e
        ))

        # Save metadata
        save_episode_metadata(
            output_dir=output_dir,
            title=title,
            description=f"AI-generated podcast about: {title}",
            duration_seconds=duration,
            speakers=speaker_names,
            style=style,
            tts_backend=tts_backend,
            source_type=source_type,
            mp3_path=output,
        )

        progress.update(task, completed=1)

    # Final summary
    console.print()
    console.print("[bold green]🎙️  Podcast generated successfully![/bold green]")
    console.print(f"  [bold]Audio:[/bold]      {output}")
    console.print(f"  [bold]Transcript:[/bold] {txt_path}")
    console.print(f"  [bold]Subtitles:[/bold]  {srt_path}")
    console.print(f"  [bold]Duration:[/bold]   {int(duration // 60)}:{int(duration % 60):02d}")

    return output
