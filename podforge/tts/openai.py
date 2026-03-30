"""OpenAI TTS backend."""
import logging
import os
from pathlib import Path

from .base import TTSBackend

logger = logging.getLogger(__name__)

AVAILABLE_VOICES = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]

DEFAULT_VOICES = {
    "host": "onyx",
    "guest": "nova",
    "narrator": "alloy",
}


class OpenAITTS(TTSBackend):
    """OpenAI text-to-speech backend."""

    def __init__(self):
        """Initialize OpenAI TTS backend."""
        self.api_key = os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OPENAI_API_KEY environment variable is not set. "
                "Get your API key at https://platform.openai.com/"
            )
        self._client = None

    @property
    def client(self):
        """Lazy-initialize the OpenAI client."""
        if self._client is None:
            import openai
            self._client = openai.OpenAI(api_key=self.api_key)
        return self._client

    @property
    def name(self) -> str:
        return "openai"

    def synthesize(self, text: str, voice: str, output_path: str) -> str:
        """Synthesize speech using OpenAI TTS.

        Args:
            text: Text to synthesize.
            voice: Voice name (alloy, echo, fable, onyx, nova, shimmer).
            output_path: Path to save the audio file.

        Returns:
            Path to the generated audio file.
        """
        voice_name = voice.lower()
        if voice_name not in AVAILABLE_VOICES:
            logger.warning(f"Unknown OpenAI voice '{voice}', falling back to 'onyx'")
            voice_name = "onyx"

        logger.info(f"Synthesizing with OpenAI TTS voice={voice_name}")

        response = self.client.audio.speech.create(
            model="tts-1-hd",
            voice=voice_name,
            input=text,
            response_format="mp3",
        )

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        response.stream_to_file(output_path)

        logger.debug(f"Saved audio to {output_path}")
        return output_path

    def list_voices(self) -> list[str]:
        """List available OpenAI TTS voices."""
        return AVAILABLE_VOICES.copy()
