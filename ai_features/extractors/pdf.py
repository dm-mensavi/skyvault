import logging

logger = logging.getLogger(__name__)


def extract_pdf(file_path: str) -> str | None:
    """
    Extracts text content from a PDF document using pdfplumber.
    """
    try:
        import pdfplumber
        extracted_pages = []

        with pdfplumber.open(file_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                text = page.extract_text()
                if text and text.strip():
                    extracted_pages.append(text.strip())

        full_text = "\n\n".join(extracted_pages)
        return full_text.strip() if full_text else ""
    except Exception as e:
        logger.error(f"pdfplumber extraction failed for {file_path}: {e}")
        return None
