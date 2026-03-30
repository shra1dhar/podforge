"""Audio mixer using FFmpeg for final podcast production."""
import logging
import subprocess
import tempfile
from pathlib import Path

from .effects import _run_ffmpeg, get_audio_duration, ensure_assets, SFX_DIR
from .music import get_intro_music, get_outro_music

logger = logging.getLogger(__name__)


def _generate_silence(duration: float, output_path: str) -> str:
    """Generate a silent audio segment.

    Args:
        duration: Duration in seconds.
        output_path: Path to save the silent audio.

    Returns:
        Path to the generated file.
    """
    _run_ffmpeg(
        ["-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono",
         "-t", str(duration), "-codec:a", "libmp3lame", "-q:a", "2",
         output_path],
        f"Generate {duration}s silence",
    )
    return output_path


def _build_concat_file(segments: list[str], concat_path: str) -> str:
    """Build an FFmpeg concat demuxer file.

    Args:
        segments: List of audio file paths.
        concat_path: Path to save the concat file.

    Returns:
        Path to the concat file.
    """
    with open(concat_path, "w") as f:
        for seg in segments:
            # Escape single quotes in paths
            escaped = seg.replace("'", "'\\''")
            f.write(f"file '{escaped}'\n")
    return concat_path


def mix_podcast(
    speech_segments: list[dict],
    output_path: str,
    work_dir: str | None = None,
    intro_music: str | None = None,
    outro_music: str | None = None,
    pause_duration: float = 0.4,
    transition_pause: float = 0.8,
) -> str:
    """Mix speech segments with music and effects into a final podcast.

    Args:
        speech_segments: List of dicts with 'audio_path' and optionally 'type' (speech/sfx).
        output_path: Path for the final MP3 output.
        work_dir: Working directory for temp files. Uses tempdir if None.
        intro_music: Custom intro music path. Uses bundled if None.
        outro_music: Custom outro music path. Uses bundled if None.
        pause_duration: Pause between speech segments in seconds.
        transition_pause: Pause around transition SFX in seconds.

    Returns:
        Path to the final mixed MP3.
    """
    ensure_assets()

    if work_dir is None:
        _tmp = tempfile.mkdtemp(prefix="podforge_mix_")
        work_dir = _tmp

    work = Path(work_dir)
    work.mkdir(parents=True, exist_ok=True)

    intro = intro_music or get_intro_music()
    outro = outro_music or get_outro_music()

    logger.info(f"Mixing {len(speech_segments)} segments into podcast...")

    # Step 1: Normalize all speech segments to consistent format
    normalized = []
    for i, seg in enumerate(speech_segments):
        seg_type = seg.get("type", "speech")

        if seg_type == "sfx":
            # SFX entries don't have audio files — handled during sequencing
            normalized.append(seg)
            continue

        audio_path = seg["audio_path"]
        norm_path = str(work / f"norm_{i:04d}.mp3")

        # Normalize to mono 44100Hz MP3
        _run_ffmpeg(
            ["-i", audio_path,
             "-ar", "44100", "-ac", "1",
             "-codec:a", "libmp3lame", "-q:a", "2",
             norm_path],
            f"Normalize segment {i}",
        )
        normalized.append({
            **seg,
            "audio_path": norm_path,
        })

    # Step 2: Build the sequence with pauses
    sequence_parts = []

    # Add intro music
    intro_norm = str(work / "intro_norm.mp3")
    _run_ffmpeg(
        ["-i", intro,
         "-ar", "44100", "-ac", "1",
         "-codec:a", "libmp3lame", "-q:a", "2",
         intro_norm],
        "Normalize intro",
    )
    sequence_parts.append(intro_norm)

    # Small pause after intro
    intro_pause = str(work / "intro_pause.mp3")
    _generate_silence(0.5, intro_pause)
    sequence_parts.append(intro_pause)

    # Add speech segments with pauses
    pause_path = str(work / "pause.mp3")
    _generate_silence(pause_duration, pause_path)

    trans_pause_path = str(work / "trans_pause.mp3")
    _generate_silence(transition_pause, trans_pause_path)

    transition_sfx = str(SFX_DIR / "transition.mp3")
    trans_sfx_norm = str(work / "transition_norm.mp3")
    _run_ffmpeg(
        ["-i", transition_sfx,
         "-ar", "44100", "-ac", "1",
         "-codec:a", "libmp3lame", "-q:a", "2",
         trans_sfx_norm],
        "Normalize transition SFX",
    )

    for i, seg in enumerate(normalized):
        seg_type = seg.get("type", "speech")

        if seg_type == "sfx":
            # Add transition sound with pauses around it
            sequence_parts.append(trans_pause_path)
            sequence_parts.append(trans_sfx_norm)
            sequence_parts.append(trans_pause_path)
        else:
            # Add speech segment with pause
            if i > 0 and normalized[i - 1].get("type") != "sfx":
                sequence_parts.append(pause_path)
            sequence_parts.append(seg["audio_path"])

    # Small pause before outro
    outro_pause = str(work / "outro_pause.mp3")
    _generate_silence(0.8, outro_pause)
    sequence_parts.append(outro_pause)

    # Add outro music
    outro_norm = str(work / "outro_norm.mp3")
    _run_ffmpeg(
        ["-i", outro,
         "-ar", "44100", "-ac", "1",
         "-codec:a", "libmp3lame", "-q:a", "2",
         outro_norm],
        "Normalize outro",
    )
    sequence_parts.append(outro_norm)

    # Step 3: Concatenate everything
    concat_file = str(work / "concat.txt")
    _build_concat_file(sequence_parts, concat_file)

    raw_output = str(work / "raw_concat.mp3")
    _run_ffmpeg(
        ["-f", "concat", "-safe", "0", "-i", concat_file,
         "-codec:a", "libmp3lame", "-q:a", "2",
         raw_output],
        "Concatenate all segments",
    )

    # Step 4: Apply loudness normalization and light compression
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    _run_ffmpeg(
        ["-i", raw_output,
         "-af", (
             "loudnorm=I=-16:LRA=11:TP=-1.5,"
             "acompressor=threshold=-20dB:ratio=3:attack=5:release=50:makeup=2"
         ),
         "-ar", "44100", "-ac", "1",
         "-codec:a", "libmp3lame", "-b:a", "192k",
         output_path],
        "Final loudness normalization and compression",
    )

    duration = get_audio_duration(output_path)
    logger.info(f"Final podcast: {output_path} ({duration:.1f}s)")

    return output_path
