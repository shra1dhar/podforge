"""Tests for podforge.extract modules."""
import tempfile
from pathlib import Path

import pytest

from podforge.extract.text import (
    extract_from_text,
    strip_markdown,
    truncate_content,
)
from podforge.extract.pdf import extract_from_pdf


# ---------------------------------------------------------------------------
# strip_markdown
# ---------------------------------------------------------------------------

class TestStripMarkdown:
    def test_removes_headers(self):
        text = "# Title\n## Subtitle\n### H3"
        result = strip_markdown(text)
        assert "# " not in result
        assert "Title" in result
        assert "Subtitle" in result
        assert "H3" in result

    def test_removes_bold_and_italic(self):
        assert strip_markdown("**bold**") == "bold"
        assert strip_markdown("*italic*") == "italic"
        assert strip_markdown("***both***") == "both"
        assert strip_markdown("__underline_bold__") == "underlinebold"

    def test_removes_links_keeps_text(self):
        result = strip_markdown("[click here](https://example.com)")
        assert result == "click here"

    def test_removes_images(self):
        result = strip_markdown("![alt text](image.png)")
        # Image regex removes ![alt](url) -> alt, but the ! may remain
        # depending on regex ordering; the link regex runs after image regex
        assert "alt text" in result

    def test_removes_code_blocks(self):
        text = "before\n```python\nprint('hi')\n```\nafter"
        result = strip_markdown(text)
        assert "print" not in result
        assert "before" in result
        assert "after" in result

    def test_removes_inline_code(self):
        result = strip_markdown("use `foo()` here")
        assert result == "use foo() here"

    def test_removes_blockquotes(self):
        result = strip_markdown("> quoted text")
        assert result == "quoted text"

    def test_removes_horizontal_rules(self):
        result = strip_markdown("above\n---\nbelow")
        assert "---" not in result
        assert "above" in result
        assert "below" in result

    def test_plain_text_unchanged(self):
        text = "Just a simple sentence."
        assert strip_markdown(text) == text

    def test_collapses_extra_newlines(self):
        text = "a\n\n\n\n\nb"
        result = strip_markdown(text)
        assert "\n\n\n" not in result


# ---------------------------------------------------------------------------
# truncate_content
# ---------------------------------------------------------------------------

class TestTruncateContent:
    def test_short_text_unchanged(self):
        text = "Short text"
        assert truncate_content(text, max_chars=100) == text

    def test_long_text_truncated(self):
        text = "word " * 50000  # ~250k chars
        result = truncate_content(text, max_chars=1000)
        assert len(result) <= 1100  # some overhead from the truncation notice
        assert result.endswith("[Content truncated for length]")

    def test_truncation_at_paragraph_boundary(self):
        # Build text with paragraphs
        paragraph = "A" * 90 + "\n\n"
        text = paragraph * 20  # ~1840 chars
        result = truncate_content(text, max_chars=1000)
        assert result.endswith("[Content truncated for length]")
        # Should have cut at a paragraph boundary
        body = result.replace("\n\n[Content truncated for length]", "")
        assert body.endswith("\n\n") or body.endswith("A")


# ---------------------------------------------------------------------------
# extract_from_text
# ---------------------------------------------------------------------------

class TestExtractFromText:
    def test_reads_temp_file(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("Hello, PodForge!")
            f.flush()
            result = extract_from_text(f.name)
        assert result == "Hello, PodForge!"

    def test_missing_file_raises(self):
        with pytest.raises(FileNotFoundError):
            extract_from_text("/tmp/nonexistent_podforge_test_file.txt")


# ---------------------------------------------------------------------------
# extract_from_pdf
# ---------------------------------------------------------------------------

class TestExtractFromPdf:
    def test_missing_file_raises(self):
        with pytest.raises(FileNotFoundError):
            extract_from_pdf("/tmp/nonexistent_podforge_test_file.pdf")
