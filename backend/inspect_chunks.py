
from app.services.document_service import extract_pdf_text
from app.services.chunking_service import chunk_pages

PDF_PATH = r"C:\Users\HP\Downloads\NIC-STA-Notification-2026.pdf"


def main():
    document = extract_pdf_text(PDF_PATH)
    chunks = chunk_pages(document["pages"])

    print("Extracted pages:", document["extracted_page_count"])
    print("Pages improved by OCR:", document["ocr_page_count"])
    print("Generated chunks:", len(chunks))

    for i, chunk in enumerate(chunks, start=1):
        if chunk["start_page"] >= 9:
            print(f"\nChunk {i}")
            print(f"Page: {chunk['start_page']}")
            print(f"Words: {len(chunk['text'].split())}")
            print(f"Preview: {chunk['text'][:250]}")


if __name__ == "__main__":
    main()
