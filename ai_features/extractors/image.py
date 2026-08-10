import logging

logger = logging.getLogger(__name__)

IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "gif", "bmp", "tiff", "tif", "webp"}


def extract_image_text(file_path: str) -> str | None:
    """
    Extracts text from images using OCR (pytesseract + Pillow).
    This enables AI processing of scanned documents, screenshots, and
    images containing visible text.

    Requires: pytesseract (+ Tesseract binary) and Pillow.
    Returns None if OCR is unavailable, or empty string if no text found.
    """
    try:
        import pytesseract
        from PIL import Image

        img = Image.open(file_path)

        # Convert palette or RGBA images to RGB for better OCR compatibility
        if img.mode in ("P", "RGBA", "LA"):
            img = img.convert("RGB")

        text = pytesseract.image_to_string(img, lang="eng")
        extracted = text.strip() if text else ""
        logger.info(f"OCR extracted {len(extracted)} chars from image '{file_path}'.")
        return extracted

    except ImportError:
        logger.warning(
            "pytesseract or Pillow not installed; image text extraction is unavailable. "
            "Install pytesseract and ensure Tesseract is on PATH to enable image OCR."
        )
        return None
    except Exception as e:
        logger.error(f"Image OCR extraction failed for {file_path}: {e}")
        return None
