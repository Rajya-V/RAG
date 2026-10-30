
from app.services.embedding_service import generate_embeddings


def test_generate_embeddings():
    texts = [
        "A primary key uniquely identifies a database row.",
        "A foreign key establishes a relationship between tables.",
    ]

    embeddings = generate_embeddings(texts)

    assert len(embeddings) == 2
    assert len(embeddings[0]) == 384
    assert len(embeddings[1]) == 384

    # Ensure vectors contain valid numerical values.
    assert all(
        isinstance(value, float)
        for vector in embeddings
        for value in vector
    )

    print("Embedding test passed!")
    print("Number of vectors:", len(embeddings))
    print("Dimensions per vector:", len(embeddings[0]))


if __name__ == "__main__":
    test_generate_embeddings()
