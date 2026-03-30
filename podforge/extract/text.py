"""Extract and process plain text and markdown content."""
import logging
import re
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

def extract_from_text(file_path: str) -> str:
    """Read text from a file (TXT, MD, etc).

    Args:
        file_path: Path to the text file.

    Returns:
        File contents as string.

    Raises:
        FileNotFoundError: If the file doesn't exist.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    text = path.read_text(encoding="utf-8")
    logger.info(f"Read {len(text)} characters from {file_path}")
    return text


def strip_markdown(text: str) -> str:
    """Strip markdown formatting to get clean text.

    Args:
        text: Markdown text.

    Returns:
        Clean text with markdown formatting removed.
    """
    # Remove headers
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
    # Remove bold/italic
    text = re.sub(r'\*{1,3}(.*?)\*{1,3}', r'\1', text)
    text = re.sub(r'_{1,3}(.*?)_{1,3}', r'\1', text)
    # Remove links but keep text
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    # Remove images
    text = re.sub(r'!\[([^\]]*)\]\([^\)]+\)', r'\1', text)
    # Remove code blocks
    text = re.sub(r'```[\s\S]*?```', '', text)
    text = re.sub(r'`([^`]+)`', r'\1', text)
    # Remove blockquotes
    text = re.sub(r'^>\s+', '', text, flags=re.MULTILINE)
    # Remove horizontal rules
    text = re.sub(r'^[-*_]{3,}\s*$', '', text, flags=re.MULTILINE)
    # Clean up extra whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def read_stdin() -> str:
    """Read text from stdin.

    Returns:
        Text read from stdin.

    Raises:
        ValueError: If stdin is empty.
    """
    if sys.stdin.isatty():
        raise ValueError("No input provided on stdin")

    text = sys.stdin.read()
    if not text.strip():
        raise ValueError("Empty input from stdin")

    logger.info(f"Read {len(text)} characters from stdin")
    return text


def truncate_content(text: str, max_chars: int = 100000) -> str:
    """Truncate text to fit within LLM context limits.

    Tries to truncate at paragraph boundaries.

    Args:
        text: Input text.
        max_chars: Maximum character count.

    Returns:
        Truncated text.
    """
    if len(text) <= max_chars:
        return text

    logger.warning(f"Content too long ({len(text)} chars), truncating to {max_chars}")
    truncated = text[:max_chars]
    # Try to break at a paragraph boundary
    last_para = truncated.rfind('\n\n')
    if last_para > max_chars * 0.8:
        truncated = truncated[:last_para]

    return truncated + "\n\n[Content truncated for length]"
