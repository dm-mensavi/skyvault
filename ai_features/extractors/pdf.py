import logging

logger = logging.getLogger(__name__)


def extract_pdf(file_path: str) -> str | None:
    """
    Extracts text content from a PDF document using pdfplumber.
    If the PDF has more than 10 pages, extracts text from the first 5 pages and last 5 pages.
    """
    try:
        import pdfplumber
        extracted_pages = []

        with pdfplumber.open(file_path) as pdf:
            total_pages = len(pdf.pages)
            if total_pages > 10:
                logger.info(
                    f"PDF '{file_path}' has {total_pages} pages (>10). "
                    f"Chunking/extracting first 5 pages (1-5) and last 5 pages ({total_pages-4}-{total_pages})."
                )
                selected_pages = list(pdf.pages[:5]) + list(pdf.pages[-5:])
            else:
                selected_pages = list(pdf.pages)

            for page in selected_pages:
                text = page.extract_text()
                if text and text.strip():
                    extracted_pages.append(text.strip())

        full_text = "\n\n".join(extracted_pages)
        return full_text.strip() if full_text else ""
    except Exception as e:
        logger.error(f"pdfplumber extraction failed for {file_path}: {e}")
        return None
