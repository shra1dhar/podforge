"""ElevenLabs TTS backend."""
import logging
import os
from pathlib import Path

from .base import TTSBackend

logger = logging.getLogger(__name__)

# Default voice mapping
DEFAULT_VOICES = {
    "host": "Rachel",
    "guest": "Adam",
    "narrator": "Bella",
}

# Known ElevenLabs voice IDs for common names
VOICE_NAME_MAP = {
    "rachel": "21m00Tcm4TlvDq8ikWAM",
    "adam": "pNInz6obpgDQGcFmaJgB",
    "bella": "EXAVITQu4vr4xnSDxMaL",
    "antoni": "ErXwobaYiN019PkySvjV",
    "domi": "AZnzlk1XvdvUeBnXmlld",
    "elli": "MF3mGyEYCl7XYWbV9V6O",
    "josh": "TxGEqnHWrfWFTfGW9XjX",
    "sam": "yoZ06aMxZJJ28mfd3POQ",
}


def _load_key_from_env_file() -> str | None:
    """Try loading ELEVENLABS_API_KEY from ~/.hermes/.env."""
    env_path = Path.home() / ".hermes" / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line.startswith("ELEVENLABS_API_KEY=") and not line.startswith("#"):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return None


class ElevenLabsTTS(TTSBackend):
    """ElevenLabs text-to-speech backend."""

    def __init__(self):
        """Initialize ElevenLabs backend."""
        self.api_key = os.environ.get("ELEVENLABS_API_KEY") or _load_key_from_env_file()
        if not self.api_key:
            raise ValueError(
                "ELEVENLABS_API_KEY environment variable is not set. "
                "Get your API key at https://elevenlabs.io/"
            )
        self._client = None

    @property
    def client(self):
        """Lazy-initialize the ElevenLabs client."""
        if self._client is None:
            from elevenlabs.client import ElevenLabs
            self._client = ElevenLabs(api_key=self.api_key)
        return self._client

    @property
    def name(self) -> str:
        return "elevenlabs"

    def _resolve_voice_id(self, voice: str) -> str:
        """Resolve a voice name to a voice ID.

        Args:
            voice: Voice name or ID.

        Returns:
            Voice ID string.
        """
        # If it looks like a voice ID already, use it directly
        if len(voice) == 20 and voice.isalnum():
            return voice

        # Check our known mapping
        voice_lower = voice.lower()
        if voice_lower in VOICE_NAME_MAP:
            return VOICE_NAME_MAP[voice_lower]

        # Try to find it via the API
        try:
            response = self.client.voices.get_all()
            for v in response.voices:
                if v.name.lower() == voice_lower:
                    return v.voice_id
        except Exception as e:
            logger.warning(f"Could not search voices via API: {e}")

        # Fall back to using the name as-is (the API might accept it)
        logger.warning(f"Could not resolve voice '{voice}', using as-is")
        return voice

    def synthesize(self, text: str, voice: str, output_path: str) -> str:
        """Synthesize speech using ElevenLabs.

        Args:
            text: Text to synthesize.
            voice: Voice name or ID.
            output_path: Path to save the MP3 file.

        Returns:
            Path to the generated audio file.
        """
        voice_id = self._resolve_voice_id(voice)
        logger.info(f"Synthesizing with ElevenLabs voice={voice} (id={voice_id})")

        audio = self.client.text_to_speech.convert(
            voice_id=voice_id,
            text=text,
            model_id="eleven_multilingual_v2",
            output_format="mp3_44100_128",
        )

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "wb") as f:
            for chunk in audio:
                f.write(chunk)

        logger.debug(f"Saved audio to {output_path}")
        return output_path

    def list_voices(self) -> list[str]:
        """List available ElevenLabs voices."""
        try:
            response = self.client.voices.get_all()
            return [v.name for v in response.voices]
        except Exception as e:
            logger.warning(f"Could not list voices: {e}")
            return list(VOICE_NAME_MAP.keys())
