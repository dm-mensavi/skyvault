import logging
import os
from .pdf import extract_pdf
from .plaintext import extract_plaintext
from .docx import extract_docx
from .image import extract_image_text

logger = logging.getLogger(__name__)

# File type extension groups
PDF_EXTENSIONS = {"pdf"}
PLAINTEXT_EXTENSIONS = {"txt", "md", "json", "py", "js", "html", "css", "csv", "xml"}
WORD_EXTENSIONS = {"docx", "doc"}
IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "gif", "bmp", "tiff", "tif", "webp"}


def extract_text(file_path: str, extension: str) -> str | None:
    """
    Main extraction dispatcher for document text processing.

    Supported file types:
      - PDF (.pdf): pdfplumber with page-sampling for large documents (>10 pages → first 5 + last 5)
      - Word (.docx, .doc): python-docx / docx2txt
      - Images (.jpg, .jpeg, .png, .gif, .bmp, .tiff, .webp): pytesseract OCR
      - Plaintext (.txt, .md, .json, .py, .js, .html, .css, .csv, .xml): built-in with encoding fallback

    Audio and video files are excluded at the upload layer (vault/views.py, vault/forms.py).

    Returns:
      str  — extracted text (may be empty string if file has no readable text)
      None — if file does not exist, type is unsupported, or an unrecoverable error occurs
    """
    if not os.path.exists(file_path):
        logger.warning(f"File path does not exist for extraction: {file_path}")
        return None

    ext = extension.lower().lstrip(".")

    if ext in PDF_EXTENSIONS:
        return extract_pdf(file_path)
    elif ext in WORD_EXTENSIONS:
        return extract_docx(file_path)
    elif ext in IMAGE_EXTENSIONS:
        return extract_image_text(file_path)
    elif ext in PLAINTEXT_EXTENSIONS:
        return extract_plaintext(file_path)

    logger.info(
        f"Extension '{ext}' is unsupported for text extraction. "
        "Audio and video files are blocked at upload; all other types are attempted."
    )
    return None
