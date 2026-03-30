"""Sound effects generation and management using FFmpeg."""
import logging
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)

ASSETS_DIR = Path(__file__).parent.parent / "assets"
SFX_DIR = ASSETS_DIR / "sfx"
MUSIC_DIR = ASSETS_DIR / "music"


def _run_ffmpeg(args: list[str], description: str = "FFmpeg command") -> None:
    """Run an FFmpeg command with error handling.

    Args:
        args: FFmpeg command arguments.
        description: Human-readable description for logging.

    Raises:
        RuntimeError: If FFmpeg fails.
    """
    cmd = ["ffmpeg", "-y"] + args
    logger.debug(f"Running: {' '.join(cmd)}")
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"{description} failed: {result.stderr}")


def ensure_assets() -> None:
    """Generate bundled audio assets if they don't exist."""
    SFX_DIR.mkdir(parents=True, exist_ok=True)
    MUSIC_DIR.mkdir(parents=True, exist_ok=True)

    generate_intro_music()
    generate_outro_music()
    generate_transition_sfx()


def generate_intro_music(output_path: str | None = None) -> str:
    """Generate a pleasant intro jingle using FFmpeg sine waves.

    Creates a bright, ascending melodic pattern that fades in.

    Args:
        output_path: Custom output path. Defaults to assets/music/intro.mp3.

    Returns:
        Path to the generated file.
    """
    if output_path is None:
        output_path = str(MUSIC_DIR / "intro.mp3")

    if Path(output_path).exists():
        return output_path

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    logger.info("Generating intro music...")

    # Create a pleasant chord progression using sine waves
    # C major chord (C4-E4-G4) -> F major (F4-A4-C5) -> G major (G4-B4-D5) -> C major
    # Duration: 5 seconds with fade in/out
    filter_complex = (
        # First chord: C major (0-1.5s)
        "sine=frequency=261.63:duration=1.5:sample_rate=44100[c4a];"
        "sine=frequency=329.63:duration=1.5:sample_rate=44100[e4a];"
        "sine=frequency=392.00:duration=1.5:sample_rate=44100[g4a];"
        "[c4a][e4a][g4a]amix=inputs=3:normalize=0[chord1];"
        # Second chord: F major (1.5-3s)
        "sine=frequency=349.23:duration=1.5:sample_rate=44100[f4];"
        "sine=frequency=440.00:duration=1.5:sample_rate=44100[a4];"
        "sine=frequency=523.25:duration=1.5:sample_rate=44100[c5a];"
        "[f4][a4][c5a]amix=inputs=3:normalize=0[chord2];"
        # Third chord: G major (3-4.5s)
        "sine=frequency=392.00:duration=1.5:sample_rate=44100[g4b];"
        "sine=frequency=493.88:duration=1.5:sample_rate=44100[b4];"
        "sine=frequency=587.33:duration=1.5:sample_rate=44100[d5];"
        "[g4b][b4][d5]amix=inputs=3:normalize=0[chord3];"
        # Final chord: C major resolve (4.5-6s)
        "sine=frequency=523.25:duration=1.5:sample_rate=44100[c5b];"
        "sine=frequency=659.25:duration=1.5:sample_rate=44100[e5];"
        "sine=frequency=783.99:duration=1.5:sample_rate=44100[g5];"
        "[c5b][e5][g5]amix=inputs=3:normalize=0[chord4];"
        # Concatenate all chords
        "[chord1][chord2][chord3][chord4]concat=n=4:v=0:a=1[melody];"
        # Apply fade in, fade out, and volume
        "[melody]afade=t=in:st=0:d=0.5,afade=t=out:st=5:d=1,volume=0.3[out]"
    )

    _run_ffmpeg(
        ["-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono",
         "-filter_complex", filter_complex,
         "-map", "[out]", "-t", "6", "-codec:a", "libmp3lame", "-q:a", "2",
         output_path],
        "Generate intro music",
    )

    logger.info(f"Intro music saved to {output_path}")
    return output_path


def generate_outro_music(output_path: str | None = None) -> str:
    """Generate a mellow outro jingle using FFmpeg sine waves.

    Creates a descending, fading melodic pattern.

    Args:
        output_path: Custom output path. Defaults to assets/music/outro.mp3.

    Returns:
        Path to the generated file.
    """
    if output_path is None:
        output_path = str(MUSIC_DIR / "outro.mp3")

    if Path(output_path).exists():
        return output_path

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    logger.info("Generating outro music...")

    # Descending pattern: G major -> F major -> C major, slower and mellower
    filter_complex = (
        # G major chord (0-2s)
        "sine=frequency=392.00:duration=2:sample_rate=44100[g4];"
        "sine=frequency=493.88:duration=2:sample_rate=44100[b4];"
        "sine=frequency=587.33:duration=2:sample_rate=44100[d5];"
        "[g4][b4][d5]amix=inputs=3:normalize=0[chord1];"
        # F major chord (2-4s)
        "sine=frequency=349.23:duration=2:sample_rate=44100[f4];"
        "sine=frequency=440.00:duration=2:sample_rate=44100[a4];"
        "sine=frequency=523.25:duration=2:sample_rate=44100[c5];"
        "[f4][a4][c5]amix=inputs=3:normalize=0[chord2];"
        # C major resolve (4-7s) - longer for resolution
        "sine=frequency=261.63:duration=3:sample_rate=44100[c4];"
        "sine=frequency=329.63:duration=3:sample_rate=44100[e4];"
        "sine=frequency=392.00:duration=3:sample_rate=44100[g4b];"
        "[c4][e4][g4b]amix=inputs=3:normalize=0[chord3];"
        # Concatenate
        "[chord1][chord2][chord3]concat=n=3:v=0:a=1[melody];"
        # Fade in slightly, fade out long
        "[melody]afade=t=in:st=0:d=0.3,afade=t=out:st=4:d=3,volume=0.25[out]"
    )

    _run_ffmpeg(
        ["-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono",
         "-filter_complex", filter_complex,
         "-map", "[out]", "-t", "7", "-codec:a", "libmp3lame", "-q:a", "2",
         output_path],
        "Generate outro music",
    )

    logger.info(f"Outro music saved to {output_path}")
    return output_path


def generate_transition_sfx(output_path: str | None = None) -> str:
    """Generate a subtle transition swoosh sound effect.

    Creates a filtered white noise swoosh.

    Args:
        output_path: Custom output path. Defaults to assets/sfx/transition.mp3.

    Returns:
        Path to the generated file.
    """
    if output_path is None:
        output_path = str(SFX_DIR / "transition.mp3")

    if Path(output_path).exists():
        return output_path

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    logger.info("Generating transition sound effect...")

    # White noise with bandpass filter, quick fade in/out for a swoosh effect
    filter_complex = (
        "anoisesrc=d=1:c=white:r=44100:a=0.3[noise];"
        "[noise]bandpass=f=2000:w=1500,"
        "afade=t=in:st=0:d=0.15,"
        "afade=t=out:st=0.4:d=0.6,"
        "volume=0.4[out]"
    )

    _run_ffmpeg(
        ["-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono",
         "-filter_complex", filter_complex,
         "-map", "[out]", "-t", "1", "-codec:a", "libmp3lame", "-q:a", "2",
         output_path],
        "Generate transition SFX",
    )

    logger.info(f"Transition SFX saved to {output_path}")
    return output_path


def get_audio_duration(file_path: str) -> float:
    """Get the duration of an audio file in seconds.

    Args:
        file_path: Path to the audio file.

    Returns:
        Duration in seconds.
    """
    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", file_path],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"ffprobe failed: {result.stderr}")
    return float(result.stdout.strip())
