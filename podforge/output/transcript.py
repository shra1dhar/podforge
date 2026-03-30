"""Transcript generation in SRT and plain text formats."""
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def generate_srt(
    script: list[dict],
    segment_durations: list[float],
    output_path: str,
    intro_duration: float = 6.5,
) -> str:
    """Generate an SRT subtitle file from the script.

    Args:
        script: List of script entries (speaker/text or sfx dicts).
        segment_durations: Duration of each speech segment in seconds.
        output_path: Path to save the SRT file.
        intro_duration: Duration of intro music in seconds.

    Returns:
        Path to the generated SRT file.
    """
    lines = []
    subtitle_index = 1
    current_time = intro_duration
    duration_idx = 0

    for entry in script:
        if "sfx" in entry:
            # Add a small gap for transitions
            current_time += 2.0
            continue

        if duration_idx >= len(segment_durations):
            break

        speaker = entry.get("speaker", "Unknown")
        text = entry.get("text", "")
        duration = segment_durations[duration_idx]
        duration_idx += 1

        start = _format_srt_time(current_time)
        end = _format_srt_time(current_time + duration)

        lines.append(str(subtitle_index))
        lines.append(f"{start} --> {end}")
        lines.append(f"[{speaker}] {text}")
        lines.append("")

        subtitle_index += 1
        current_time += duration + 0.4  # Add pause between segments

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    logger.info(f"SRT transcript saved to {output_path}")
    return output_path


def generate_text_transcript(
    script: list[dict],
    output_path: str,
    title: str = "Podcast Episode",
) -> str:
    """Generate a plain text transcript from the script.

    Args:
        script: List of script entries.
        output_path: Path to save the transcript.
        title: Episode title for the header.

    Returns:
        Path to the generated transcript file.
    """
    lines = [
        f"TRANSCRIPT: {title}",
        "=" * (len(title) + 13),
        "",
    ]

    for entry in script:
        if "sfx" in entry:
            lines.append(f"[{entry['sfx'].upper()}]")
            lines.append("")
        elif "speaker" in entry:
            speaker = entry["speaker"].upper()
            text = entry["text"]
            lines.append(f"{speaker}: {text}")
            lines.append("")

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    logger.info(f"Text transcript saved to {output_path}")
    return output_path


def _format_srt_time(seconds: float) -> str:
    """Format seconds to SRT time format (HH:MM:SS,mmm).

    Args:
        seconds: Time in seconds.

    Returns:
        Formatted SRT time string.
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
