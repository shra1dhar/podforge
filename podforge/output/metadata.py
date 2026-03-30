"""Episode metadata and ID3 tag management."""
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from mutagen.id3 import ID3, TIT2, TPE1, TALB, TDRC, TCON, COMM, ID3NoHeaderError
from mutagen.mp3 import MP3

logger = logging.getLogger(__name__)


def apply_id3_tags(
    mp3_path: str,
    title: str = "Podcast Episode",
    artist: str = "PodForge AI",
    album: str = "PodForge Podcast",
    description: str = "",
    genre: str = "Podcast",
    year: str | None = None,
) -> None:
    """Apply ID3 tags to an MP3 file.

    Args:
        mp3_path: Path to the MP3 file.
        title: Episode title.
        artist: Artist/creator name.
        album: Album/podcast name.
        description: Episode description.
        genre: Genre tag.
        year: Year string. Defaults to current year.
    """
    if year is None:
        year = str(datetime.now(timezone.utc).year)

    logger.info(f"Applying ID3 tags to {mp3_path}")

    try:
        audio = MP3(mp3_path, ID3=ID3)
        try:
            audio.add_tags()
        except Exception:
            pass  # Tags already exist
    except ID3NoHeaderError:
        audio = MP3(mp3_path)
        audio.add_tags()

    audio.tags.add(TIT2(encoding=3, text=title))
    audio.tags.add(TPE1(encoding=3, text=artist))
    audio.tags.add(TALB(encoding=3, text=album))
    audio.tags.add(TDRC(encoding=3, text=year))
    audio.tags.add(TCON(encoding=3, text=genre))

    if description:
        audio.tags.add(COMM(encoding=3, lang="eng", desc="", text=description))

    audio.save()
    logger.info("ID3 tags applied successfully")


def save_episode_metadata(
    output_dir: str,
    title: str,
    description: str,
    duration_seconds: float,
    speakers: list[str],
    style: str,
    tts_backend: str,
    source_type: str,
    mp3_path: str,
) -> str:
    """Save episode metadata as JSON.

    Args:
        output_dir: Directory to save metadata.
        title: Episode title.
        description: Episode description.
        duration_seconds: Episode duration in seconds.
        speakers: List of speaker names.
        style: Podcast style used.
        tts_backend: TTS backend used.
        source_type: Input source type.
        mp3_path: Path to the output MP3.

    Returns:
        Path to the metadata JSON file.
    """
    metadata = {
        "title": title,
        "description": description,
        "duration_seconds": round(duration_seconds, 1),
        "duration_formatted": _format_duration(duration_seconds),
        "speakers": speakers,
        "style": style,
        "tts_backend": tts_backend,
        "source_type": source_type,
        "mp3_file": str(Path(mp3_path).name),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "generator": "PodForge v0.1.0",
    }

    output_path = str(Path(output_dir) / "episode_metadata.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    logger.info(f"Episode metadata saved to {output_path}")
    return output_path


def _format_duration(seconds: float) -> str:
    """Format seconds into MM:SS string."""
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes}:{secs:02d}"
