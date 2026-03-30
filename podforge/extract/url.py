"""Extract clean text content from URLs."""
import logging
from trafilatura import fetch_url, extract

logger = logging.getLogger(__name__)

def extract_from_url(url: str) -> str:
    """Fetch and extract clean text from a URL.

    Args:
        url: The URL to extract text from.

    Returns:
        Extracted text content.

    Raises:
        ValueError: If the URL cannot be fetched or no text extracted.
    """
    logger.info(f"Fetching URL: {url}")
    downloaded = fetch_url(url)
    if downloaded is None:
        raise ValueError(f"Failed to fetch URL: {url}")

    text = extract(downloaded, include_comments=False, include_tables=True)
    if not text:
        raise ValueError(f"No text content could be extracted from: {url}")

    logger.info(f"Extracted {len(text)} characters from URL")
    return text
