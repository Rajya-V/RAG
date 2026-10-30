
from functools import lru_cache
from pathlib import Path

import chromadb

# Keep persistent vector data inside the backend directory.
BACKEND_DIR = Path(__file__).resolve().parents[2]
CHROMA_DIR = BACKEND_DIR / "storage" / "chroma"

COLLECTION_NAME = "enterprise_knowledge"


@lru_cache(maxsize=1)
def get_vector_collection():
    """
    Create or reopen the persistent ChromaDB collection.
    """
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)

    client = chromadb.PersistentClient(
        path=str(CHROMA_DIR)
    )

    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


def store_chunks(
    chunks: list[dict],
    embeddings: list[list[float]],
    document_id: str,
    filename: str,
) -> int:
    """
    Store chunks, embeddings, and source metadata.
    Returns the number of stored chunks.
    """
    if len(chunks) != len(embeddings):
        raise ValueError(
            "Each chunk must have exactly one embedding."
        )

    if not chunks:
        return 0

    collection = get_vector_collection()

    ids = [
        f"{document_id}_{chunk['chunk_id']}"
        for chunk in chunks
    ]

    documents = [chunk["text"] for chunk in chunks]

    metadatas = [
        {
            "document_id": document_id,
            "filename": filename,
            "start_page": int(chunk["start_page"]),
            "end_page": int(chunk["end_page"]),
            "start_word": int(chunk["start_word"]),
            "end_word": int(chunk["end_word"]),
        }
        for chunk in chunks
    ]

    collection.upsert(
        ids=ids,
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas,
    )

    return len(ids)
def delete_document_chunks(document_id: str) -> int:
    """
    Delete all chunks belonging to a specific document.
    Returns the number of chunks deleted.
    """
    if not document_id.strip():
        raise ValueError("document_id cannot be empty.")

    collection = get_vector_collection()

    results = collection.get(
        where={"document_id": document_id},
        include=[],
    )

    chunk_ids = results["ids"]

    if not chunk_ids:
        return 0

    collection.delete(ids=chunk_ids)

    return len(chunk_ids)
