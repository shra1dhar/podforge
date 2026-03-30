"""Edge TTS (free) backend."""
import asyncio
import logging
from pathlib import Path

import edge_tts

from .base import TTSBackend

logger = logging.getLogger(__name__)

# Default voice mapping for edge-tts
DEFAULT_VOICES = {
    "host": "en-US-GuyNeural",
    "guest": "en-US-JennyNeural",
    "narrator": "en-US-AriaNeural",
}

# Curated list of good English voices
VOICE_SHORTCUTS = {
    "guy": "en-US-GuyNeural",
    "jenny": "en-US-JennyNeural",
    "aria": "en-US-AriaNeural",
    "davis": "en-US-DavisNeural",
    "jane": "en-US-JaneNeural",
    "jason": "en-US-JasonNeural",
    "sara": "en-US-SaraNeural",
    "tony": "en-US-TonyNeural",
    "nancy": "en-US-NancyNeural",
    "ryan": "en-GB-RyanNeural",
    "sonia": "en-GB-SoniaNeural",
    "natasha": "en-AU-NatashaNeural",
    "william": "en-AU-WilliamNeural",
}


class EdgeTTS(TTSBackend):
    """Edge TTS (free) text-to-speech backend."""

    @property
    def name(self) -> str:
        return "edge"

    def _resolve_voice(self, voice: str) -> str:
        """Resolve a voice shortcut to full voice name.

        Args:
            voice: Voice shortcut or full name.

        Returns:
            Full voice name for edge-tts.
        """
        voice_lower = voice.lower()
        if voice_lower in VOICE_SHORTCUTS:
            return VOICE_SHORTCUTS[voice_lower]
        # If it already looks like a full voice name, use it
        if "-" in voice and "Neural" in voice:
            return voice
        # Default fallback
        logger.warning(f"Unknown voice '{voice}', falling back to en-US-GuyNeural")
        return "en-US-GuyNeural"

    async def _synthesize_async(self, text: str, voice: str, output_path: str) -> str:
        """Async implementation of synthesis.

        Args:
            text: Text to synthesize.
            voice: Voice name.
            output_path: Output file path.

        Returns:
            Path to the generated audio file.
        """
        full_voice = self._resolve_voice(voice)
        logger.info(f"Synthesizing with Edge TTS voice={full_voice}")

        communicate = edge_tts.Communicate(text, full_voice)
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        await communicate.save(output_path)

        logger.debug(f"Saved audio to {output_path}")
        return output_path

    def synthesize(self, text: str, voice: str, output_path: str) -> str:
        """Synthesize speech using Edge TTS.

        Args:
            text: Text to synthesize.
            voice: Voice name or shortcut.
            output_path: Path to save the audio file.

        Returns:
            Path to the generated audio file.
        """
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            # We're already in an async context, create a new thread
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(
                    asyncio.run,
                    self._synthesize_async(text, voice, output_path),
                )
                return future.result()
        else:
            return asyncio.run(self._synthesize_async(text, voice, output_path))

    def list_voices(self) -> list[str]:
        """List available Edge TTS voices."""
        return list(VOICE_SHORTCUTS.keys())
