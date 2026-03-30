"""Base interface for TTS backends."""
from abc import ABC, abstractmethod
from pathlib import Path


class TTSBackend(ABC):
    """Abstract base class for text-to-speech backends."""

    @abstractmethod
    def synthesize(self, text: str, voice: str, output_path: str) -> str:
        """Synthesize speech from text.

        Args:
            text: The text to synthesize.
            voice: Voice identifier/name.
            output_path: Path to save the audio file.

        Returns:
            Path to the generated audio file.
        """
        ...

    @abstractmethod
    def list_voices(self) -> list[str]:
        """List available voices.

        Returns:
            List of voice names/identifiers.
        """
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """Backend name."""
        ...
