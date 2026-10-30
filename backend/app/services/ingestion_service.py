
#ingestion_service.py
from pathlib import Path
from uuid import uuid4

from app.services.chunking_service import chunk_pages
from app.services.document_service import extract_pdf_text
from app.services.embedding_service import generate_embeddings
from app.services.vector_store_service import store_chunks


def ingest_pdf(
    file_path: str | Path,
    document_id: str | None = None,
) -> dict:
    """
    Extract PDF text, create chunks, generate embeddings,
    and store chunks in the local vector database.

    A document ID can be supplied when re-indexing an existing
    document. Existing chunks should be deleted separately first.
    """
    document = extract_pdf_text(file_path)
    chunks = chunk_pages(document["pages"])

    document_id = document_id or str(uuid4())

    if chunks:
        texts = [chunk["text"] for chunk in chunks]
        embeddings = generate_embeddings(texts)

        stored_count = store_chunks(
            chunks=chunks,
            embeddings=embeddings,
            document_id=document_id,
            filename=document["filename"],
        )
    else:
        stored_count = 0

    return {
        "document_id": document_id,
        "filename": document["filename"],
        "page_count": document["page_count"],
        "extracted_page_count": document["extracted_page_count"],
        "ocr_page_count": document["ocr_page_count"],
        "chunk_count": len(chunks),
        "stored_chunk_count": stored_count,
        "chunks": chunks,
    }
