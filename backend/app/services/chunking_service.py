
from uuid import uuid4

CHUNK_SIZE = 300
CHUNK_OVERLAP = 50


def chunk_pages(pages: list[dict]) -> list[dict]:
    """Create overlapping chunks without combining separate pages."""
    if CHUNK_SIZE <= CHUNK_OVERLAP:
        raise ValueError(
            "CHUNK_SIZE must be greater than CHUNK_OVERLAP."
        )

    chunks = []
    step = CHUNK_SIZE - CHUNK_OVERLAP

    for page in pages:
        page_number = page["page_number"]
        text = page["text"].strip()

        if not text:
            continue

        words = text.split()

        for start in range(0, len(words), step):
            window = words[start:start + CHUNK_SIZE]

            if not window:
                continue

            chunks.append({
                "chunk_id": str(uuid4()),
                "start_word": start,
                "end_word": start + len(window),
                "start_page": page_number,
                "end_page": page_number,
                "text": " ".join(window),
            })

            if start + CHUNK_SIZE >= len(words):
                break

    return chunks
