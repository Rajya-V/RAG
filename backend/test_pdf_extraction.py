
import tempfile
from pathlib import Path

import pymupdf

from app.services.document_service import (
    DocumentProcessingError,
    extract_pdf_text,
)


def create_sample_pdf(file_path: Path) -> None:
    """Create a small PDF containing known text."""
    with pymupdf.open() as pdf:
        page = pdf.new_page()
        page.insert_text(
            (72, 72),
            "Enterprise Knowledge Copilot PDF extraction test."
        )
        pdf.save(file_path)


def main() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        pdf_path = Path(temp_dir) / "sample.pdf"
        create_sample_pdf(pdf_path)

        result = extract_pdf_text(pdf_path)

        print("PDF extraction successful!")
        print("Filename:", result["filename"])
        print("Total pages:", result["page_count"])
        print("Pages with text:", result["extracted_page_count"])
        print("Extracted text:", result["pages"][0]["text"])

        assert result["page_count"] == 1
        assert result["extracted_page_count"] == 1
        assert (
            "Enterprise Knowledge Copilot"
            in result["pages"][0]["text"]
        )

        print("\nAll assertions passed!")


if __name__ == "__main__":
    main()
