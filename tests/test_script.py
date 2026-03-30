"""Tests for podforge.script modules."""
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from podforge.script.prompts import build_system_prompt, build_user_prompt
from podforge.script.generator import generate_script, save_script, load_script


# ---------------------------------------------------------------------------
# build_system_prompt
# ---------------------------------------------------------------------------

class TestBuildSystemPrompt:
    def test_casual_style(self):
        prompt = build_system_prompt(style="casual")
        assert "casual" in prompt.lower() or "coffee shop" in prompt.lower()
        assert "Alex" in prompt
        assert "Sam" in prompt

    def test_academic_style(self):
        prompt = build_system_prompt(style="academic")
        assert "seminar" in prompt.lower() or "scholarly" in prompt.lower()

    def test_debate_style(self):
        prompt = build_system_prompt(style="debate")
        assert "debate" in prompt.lower()

    def test_storytelling_style(self):
        prompt = build_system_prompt(style="storytelling")
        assert "narrative" in prompt.lower() or "stories" in prompt.lower()

    def test_custom_speaker_names(self):
        prompt = build_system_prompt(speaker_names=["Alice", "Bob"])
        assert "Alice" in prompt
        assert "Bob" in prompt
        # Default names should NOT be present
        assert "Alex, Sam" not in prompt

    def test_unknown_style_falls_back_to_casual(self):
        prompt = build_system_prompt(style="nonexistent")
        casual_prompt = build_system_prompt(style="casual")
        # Both should contain the casual style text
        assert "coffee shop" in prompt.lower()
        assert "coffee shop" in casual_prompt.lower()

    def test_length_affects_target_lines(self):
        short = build_system_prompt(length_minutes=5)
        long = build_system_prompt(length_minutes=30)
        # 5 min -> 75 lines, 30 min -> 450 lines
        assert "75" in short
        assert "450" in long


# ---------------------------------------------------------------------------
# build_user_prompt
# ---------------------------------------------------------------------------

class TestBuildUserPrompt:
    def test_includes_content(self):
        prompt = build_user_prompt("Some fascinating topic")
        assert "Some fascinating topic" in prompt

    def test_includes_instructions(self):
        prompt = build_user_prompt("anything")
        assert "YAML" in prompt


# ---------------------------------------------------------------------------
# save_script / load_script roundtrip
# ---------------------------------------------------------------------------

class TestSaveLoadScript:
    def test_roundtrip(self):
        script = [
            {"speaker": "Alex", "text": "Hello there!"},
            {"sfx": "transition"},
            {"speaker": "Sam", "text": "Hey Alex, welcome back."},
        ]
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as f:
            path = f.name

        save_script(script, path)
        loaded = load_script(path)

        assert len(loaded) == 3
        assert loaded[0]["speaker"] == "Alex"
        assert loaded[0]["text"] == "Hello there!"
        assert loaded[1]["sfx"] == "transition"
        assert loaded[2]["speaker"] == "Sam"

    def test_load_invalid_yaml_raises(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as f:
            f.write("not_a_list: true\nkey: value\n")
            path = f.name

        with pytest.raises(ValueError, match="YAML list"):
            load_script(path)

    def test_load_missing_file_raises(self):
        with pytest.raises(FileNotFoundError):
            load_script("/tmp/nonexistent_podforge_script.yaml")


# ---------------------------------------------------------------------------
# generate_script
# ---------------------------------------------------------------------------

class TestGenerateScript:
    def test_raises_without_api_key(self):
        with patch.dict("os.environ", {}, clear=True):
            # Ensure ANTHROPIC_API_KEY is absent
            import os
            os.environ.pop("ANTHROPIC_API_KEY", None)
            with pytest.raises(ValueError, match="ANTHROPIC_API_KEY"):
                generate_script("test content")
