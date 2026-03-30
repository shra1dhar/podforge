"""Tests for podforge.tts backends."""
from unittest.mock import patch

import pytest

from podforge.tts.edge import EdgeTTS


# ---------------------------------------------------------------------------
# EdgeTTS._resolve_voice
# ---------------------------------------------------------------------------

class TestEdgeTTSResolveVoice:
    def setup_method(self):
        self.tts = EdgeTTS()

    def test_resolves_shortcut(self):
        assert self.tts._resolve_voice("guy") == "en-US-GuyNeural"
        assert self.tts._resolve_voice("jenny") == "en-US-JennyNeural"
        assert self.tts._resolve_voice("Guy") == "en-US-GuyNeural"

    def test_passes_through_full_name(self):
        full = "en-US-DavisNeural"
        assert self.tts._resolve_voice(full) == full

    def test_unknown_voice_falls_back(self):
        result = self.tts._resolve_voice("nonexistent_voice")
        assert result == "en-US-GuyNeural"


# ---------------------------------------------------------------------------
# ElevenLabsTTS - requires API key
# ---------------------------------------------------------------------------

class TestElevenLabsTTSInit:
    def test_raises_without_api_key(self):
        with patch.dict("os.environ", {}, clear=True):
            import os
            os.environ.pop("ELEVENLABS_API_KEY", None)
            from podforge.tts.elevenlabs import ElevenLabsTTS
            with pytest.raises(ValueError, match="ELEVENLABS_API_KEY"):
                ElevenLabsTTS()


# ---------------------------------------------------------------------------
# OpenAITTS - requires API key
# ---------------------------------------------------------------------------

class TestOpenAITTSInit:
    def test_raises_without_api_key(self):
        with patch.dict("os.environ", {}, clear=True):
            import os
            os.environ.pop("OPENAI_API_KEY", None)
            from podforge.tts.openai import OpenAITTS
            with pytest.raises(ValueError, match="OPENAI_API_KEY"):
                OpenAITTS()
