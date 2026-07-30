import logging
import os
from .pdf import extract_pdf
from .plaintext import extract_plaintext

logger = logging.getLogger(__name__)

PLAINTEXT_EXTENSIONS = {"txt", "md", "json", "py", "js", "html", "css", "csv", "xml"}
PDF_EXTENSIONS = {"pdf"}


def extract_text(file_path: str, extension: str) -> str | None:
    """
    Main extraction dispatcher for document text processing.
    Returns extracted text string, empty string if no text found, or None if unsupported/error.
    """
    if not os.path.exists(file_path):
        logger.warning(f"File path does not exist for extraction: {file_path}")
        return None

    ext = extension.lower().lstrip(".")

    if ext in PDF_EXTENSIONS:
        return extract_pdf(file_path)
    elif ext in PLAINTEXT_EXTENSIONS:
        return extract_plaintext(file_path)

    logger.info(f"Extension '{ext}' is unsupported for text extraction.")
    return None
