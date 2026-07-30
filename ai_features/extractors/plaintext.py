import logging

logger = logging.getLogger(__name__)


def extract_plaintext(file_path: str) -> str | None:
    """
    Extracts text from plain text and code files with encoding fallbacks.
    """
    encodings = ["utf-8", "utf-8-sig", "latin-1", "cp1252"]

    for enc in encodings:
        try:
            with open(file_path, "r", encoding=enc) as f:
                content = f.read()
                if content and content.strip():
                    return content.strip()
                return ""
        except UnicodeDecodeError:
            continue
        except Exception as e:
            logger.error(f"Error reading plaintext file {file_path} with encoding {enc}: {e}")
            break

    logger.warning(f"Unable to decode plaintext file {file_path} with any supported encoding.")
    return None
