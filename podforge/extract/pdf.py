"""Extract text from PDF files."""
import logging
from pathlib import Path
import pdfplumber

logger = logging.getLogger(__name__)

def extract_from_pdf(file_path: str) -> str:
    """Extract text from a PDF file.

    Args:
        file_path: Path to the PDF file.

    Returns:
        Extracted text content.

    Raises:
        FileNotFoundError: If the file doesn't exist.
        ValueError: If no text could be extracted.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF file not found: {file_path}")

    logger.info(f"Extracting text from PDF: {file_path}")
    pages_text = []

    with pdfplumber.open(path) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text()
            if text:
                pages_text.append(text)
            logger.debug(f"Processed page {i + 1}/{len(pdf.pages)}")

    if not pages_text:
        raise ValueError(f"No text could be extracted from PDF: {file_path}")

    full_text = "\n\n".join(pages_text)
    logger.info(f"Extracted {len(full_text)} characters from {len(pages_text)} pages")
    return full_text
