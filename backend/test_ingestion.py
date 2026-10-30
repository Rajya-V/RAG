
import tempfile
from pathlib import Path

import pymupdf

from app.services.ingestion_service import ingest_pdf


def main():
    with tempfile.TemporaryDirectory() as temp_dir:
        pdf_path = Path(temp_dir) / "sample.pdf"

        with pymupdf.open() as pdf:
            page = pdf.new_page()
            page.insert_text(
                (72, 72),
                "Enterprise Knowledge Copilot " * 80,
            )
            pdf.save(pdf_path)

        result = ingest_pdf(pdf_path)

        assert result["filename"] == "sample.pdf"
        assert result["page_count"] == 1
        assert result["chunk_count"] >= 1
        assert result["chunks"][0]["page_number"] == 1

        print("Ingestion pipeline test passed!")
        print("Filename:", result["filename"])
        print("Pages:", result["page_count"])
        print("Chunks:", result["chunk_count"])
        print("First chunk ID:", result["chunks"][0]["chunk_id"])
        print("First chunk text:", result["chunks"][0]["text"][:150])


if __name__ == "__main__":
    main()
