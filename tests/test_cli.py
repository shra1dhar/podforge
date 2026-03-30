"""Tests for podforge.cli module."""
import pytest
from click.testing import CliRunner

from podforge.cli import cli


# ---------------------------------------------------------------------------
# CLI basic options
# ---------------------------------------------------------------------------

class TestCLI:
    def setup_method(self):
        self.runner = CliRunner()

    def test_help(self):
        result = self.runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "PodForge" in result.output
        assert "--url" in result.output
        assert "--file" in result.output

    def test_version(self):
        result = self.runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert "podforge" in result.output.lower()
        assert "0.1.0" in result.output

    def test_no_input_shows_error(self):
        result = self.runner.invoke(cli, [])
        assert result.exit_code != 0
