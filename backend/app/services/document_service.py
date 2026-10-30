
from pathlib import Path

import pymupdf
import pytesseract
from PIL import Image
import re
import unicodedata

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
MAX_PAGES = 100
MIN_TEXT_WORDS = 50

# Configure the Tesseract executable on Windows.
pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)


class DocumentProcessingError(Exception):
    """Raised when a document cannot be processed safely."""

def clean_extracted_text(text: str) -> str:
    """Normalize PDF/OCR text while preserving its meaning."""
    text = unicodedata.normalize("NFKC", text)

    # Remove invisible and control characters, preserving line breaks.
    text = "".join(
        char for char in text
        if char in "\n\t" or unicodedata.category(char) != "Cc"
    )

    # Fix common PDF extraction ligatures.
    replacements = {
        "\ufb01": "fi",
        "\ufb02": "fl",
        "\ufb00": "ff",
        "\ufb03": "ffi",
        "\ufb04": "ffl",
        "\ufffd": "",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    # Normalize whitespace within lines.
    lines = [
        re.sub(r"[ \t]+", " ", line).strip()
        for line in text.splitlines()
    ]

    # Keep paragraph breaks, but remove excessive blank lines.
    text = "\n".join(lines)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()

def extract_pdf_text(file_path: str | Path) -> dict:
    path = Path(file_path)

    if not path.exists() or not path.is_file():
        raise DocumentProcessingError("PDF file was not found.")

    if path.suffix.lower() != ".pdf":
        raise DocumentProcessingError("Only PDF files are supported.")

    if path.stat().st_size > MAX_FILE_SIZE:
        raise DocumentProcessingError("PDF exceeds the 10 MB size limit.")

    try:
        with pymupdf.open(path) as pdf:
            if pdf.is_encrypted:
                raise DocumentProcessingError(
                    "Password-protected PDFs are not supported."
                )

            if len(pdf) == 0:
                raise DocumentProcessingError("PDF contains no pages.")

            if len(pdf) > MAX_PAGES:
                raise DocumentProcessingError(
                    "PDF exceeds the 100-page limit."
                )

            pages = []
            ocr_page_count = 0

            for page_number, page in enumerate(pdf, start=1):
                text = clean_extracted_text(page.get_text())

                # Use OCR when native PDF text is insufficient.
                if len(text.split()) < MIN_TEXT_WORDS:
                    pix = page.get_pixmap(
                        matrix=pymupdf.Matrix(2, 2),
                        alpha=False,
                    )

                    image = Image.frombytes(
                        "RGB",
                        [pix.width, pix.height],
                        pix.samples,
                    )

                    ocr_text = clean_extracted_text(
                        pytesseract.image_to_string(image, lang="eng")
                    )

                    # Keep whichever extraction produced more words.
                    if len(ocr_text.split()) > len(text.split()):
                        text = ocr_text
                        ocr_page_count += 1

                if text:
                    pages.append({
                        "page_number": page_number,
                        "text": text,
                    })

            if not pages:
                raise DocumentProcessingError(
                    "No extractable text found. "
                    "The PDF may contain scanned images."
                )

            return {
                "filename": path.name,
                "page_count": len(pdf),
                "extracted_page_count": len(pages),
                "ocr_page_count": ocr_page_count,
                "pages": pages,
            }

    except DocumentProcessingError:
        raise
    except Exception as exc:
        raise DocumentProcessingError(
            "The PDF could not be read. Check that it is a valid PDF "
            "and that OCR is configured correctly."
        ) from exc
