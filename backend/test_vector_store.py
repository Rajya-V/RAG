
from uuid import uuid4

from app.services.embedding_service import generate_embeddings
from app.services.vector_store_service import (
    get_vector_collection,
    store_chunks,
)


def test_store_chunks():
    document_id = str(uuid4())

    chunks = [
        {
            "chunk_id": str(uuid4()),
            "start_page": 1,
            "end_page": 1,
            "start_word": 0,
            "end_word": 10,
            "text": "A primary key uniquely identifies a database row.",
        },
        {
            "chunk_id": str(uuid4()),
            "start_page": 1,
            "end_page": 2,
            "start_word": 250,
            "end_word": 260,
            "text": "A foreign key establishes relationships between tables.",
        },
    ]

    texts = [chunk["text"] for chunk in chunks]
    embeddings = generate_embeddings(texts)

    stored_count = store_chunks(
        chunks=chunks,
        embeddings=embeddings,
        document_id=document_id,
        filename="test_database.pdf",
    )

    assert stored_count == 2

    collection = get_vector_collection()
    results = collection.get(
        where={"document_id": document_id},
        include=["documents", "metadatas"],
    )

    assert len(results["ids"]) == 2
    assert results["documents"][0] is not None
    assert results["metadatas"][0]["filename"] == "test_database.pdf"

    print("Vector-store test passed!")
    print("Stored chunks:", stored_count)


if __name__ == "__main__":
    test_store_chunks()
