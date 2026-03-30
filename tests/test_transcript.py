"""Tests for podforge.output.transcript module."""
import tempfile
from pathlib import Path

import pytest

from podforge.output.transcript import (
    generate_srt,
    generate_text_transcript,
    _format_srt_time,
)


# ---------------------------------------------------------------------------
# _format_srt_time
# ---------------------------------------------------------------------------

class TestFormatSrtTime:
    def test_zero(self):
        assert _format_srt_time(0.0) == "00:00:00,000"

    def test_seconds_only(self):
        assert _format_srt_time(5.5) == "00:00:05,500"

    def test_minutes_and_seconds(self):
        assert _format_srt_time(125.25) == "00:02:05,250"

    def test_hours(self):
        # 3661.0 avoids floating-point rounding issues with 3661.1
        assert _format_srt_time(3661.0) == "01:01:01,000"

    def test_fractional_millis(self):
        # 0.123 seconds -> 123 ms
        assert _format_srt_time(0.123) == "00:00:00,123"


# ---------------------------------------------------------------------------
# generate_srt
# ---------------------------------------------------------------------------

class TestGenerateSrt:
    def test_produces_valid_srt(self):
        script = [
            {"speaker": "Alex", "text": "Hello everyone."},
            {"speaker": "Sam", "text": "Great to be here!"},
        ]
        durations = [2.5, 3.0]

        with tempfile.TemporaryDirectory() as tmpdir:
            out = Path(tmpdir) / "test.srt"
            result = generate_srt(script, durations, str(out), intro_duration=0.0)

            assert Path(result).exists()
            content = Path(result).read_text()

            # SRT index numbers
            assert "1\n" in content
            assert "2\n" in content
            # Time arrows
            assert "-->" in content
            # Speaker labels
            assert "[Alex]" in content
            assert "[Sam]" in content

    def test_sfx_entries_skipped_in_srt(self):
        script = [
            {"speaker": "Alex", "text": "Before transition."},
            {"sfx": "transition"},
            {"speaker": "Sam", "text": "After transition."},
        ]
        durations = [2.0, 3.0]

        with tempfile.TemporaryDirectory() as tmpdir:
            out = Path(tmpdir) / "test.srt"
            content_path = generate_srt(script, durations, str(out), intro_duration=0.0)
            content = Path(content_path).read_text()

            # Should have 2 subtitle entries, not 3
            assert "[Alex]" in content
            assert "[Sam]" in content
            assert "transition" not in content.lower().split("[sam]")[0].split("[alex]")[0]


# ---------------------------------------------------------------------------
# generate_text_transcript
# ---------------------------------------------------------------------------

class TestGenerateTextTranscript:
    def test_produces_formatted_text(self):
        script = [
            {"speaker": "Alex", "text": "Welcome to the show."},
            {"sfx": "transition"},
            {"speaker": "Sam", "text": "Thanks for having me."},
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            out = Path(tmpdir) / "transcript.txt"
            result = generate_text_transcript(script, str(out), title="Test Episode")

            content = Path(result).read_text()

            assert "TRANSCRIPT: Test Episode" in content
            assert "ALEX: Welcome to the show." in content
            assert "[TRANSITION]" in content
            assert "SAM: Thanks for having me." in content
