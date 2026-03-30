"""Tests for podforge.output.metadata module."""
import json
import tempfile
from pathlib import Path

import pytest

from podforge.output.metadata import save_episode_metadata, _format_duration


# ---------------------------------------------------------------------------
# _format_duration
# ---------------------------------------------------------------------------

class TestFormatDuration:
    def test_zero(self):
        assert _format_duration(0) == "0:00"

    def test_seconds_only(self):
        assert _format_duration(45) == "0:45"

    def test_minutes_and_seconds(self):
        assert _format_duration(125) == "2:05"

    def test_exact_minute(self):
        assert _format_duration(60) == "1:00"

    def test_large_value(self):
        assert _format_duration(3661) == "61:01"


# ---------------------------------------------------------------------------
# save_episode_metadata
# ---------------------------------------------------------------------------

class TestSaveEpisodeMetadata:
    def test_creates_valid_json(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = save_episode_metadata(
                output_dir=tmpdir,
                title="Test Episode",
                description="A test episode.",
                duration_seconds=305.7,
                speakers=["Alex", "Sam"],
                style="casual",
                tts_backend="edge",
                source_type="topic",
                mp3_path="/tmp/episode.mp3",
            )

            assert Path(result).exists()
            with open(result) as f:
                data = json.load(f)

            assert data["title"] == "Test Episode"
            assert data["description"] == "A test episode."
            assert data["duration_seconds"] == 305.7
            assert data["duration_formatted"] == "5:05"
            assert data["speakers"] == ["Alex", "Sam"]
            assert data["style"] == "casual"
            assert data["tts_backend"] == "edge"
            assert data["source_type"] == "topic"
            assert data["mp3_file"] == "episode.mp3"
            assert "created_at" in data
            assert "generator" in data
