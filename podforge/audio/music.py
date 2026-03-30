"""Music handling for podcast episodes."""
import logging
from pathlib import Path

from .effects import MUSIC_DIR, ensure_assets

logger = logging.getLogger(__name__)


def get_intro_music() -> str:
    """Get the path to intro music, generating it if needed.

    Returns:
        Path to intro music file.
    """
    intro_path = MUSIC_DIR / "intro.mp3"
    if not intro_path.exists():
        ensure_assets()
    return str(intro_path)


def get_outro_music() -> str:
    """Get the path to outro music, generating it if needed.

    Returns:
        Path to outro music file.
    """
    outro_path = MUSIC_DIR / "outro.mp3"
    if not outro_path.exists():
        ensure_assets()
    return str(outro_path)


def get_custom_music(path: str) -> str:
    """Validate and return a custom music file path.

    Args:
        path: Path to custom music file.

    Returns:
        Validated path string.

    Raises:
        FileNotFoundError: If the file doesn't exist.
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Custom music file not found: {path}")
    return str(p)
