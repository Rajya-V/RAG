
from app.services.chunking_service import (
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    chunk_pages,
)



def test_chunk_pages_uses_size_and_overlap():
    words = [f"word{i}" for i in range(700)]

    pages = [
        {"page_number": 1, "text": " ".join(words[:350])},
        {"page_number": 2, "text": " ".join(words[350:])},
    ]

    chunks = chunk_pages(pages)

    assert CHUNK_SIZE == 300
    assert CHUNK_OVERLAP == 50
    assert len(chunks) == 4

    expected_sizes = [300, 100, 300, 100]
    assert [
        len(chunk["text"].split()) for chunk in chunks
    ] == expected_sizes

    # Verify overlap within each page.
    for first, second in [(chunks[0], chunks[1]), (chunks[2], chunks[3])]:
        first_words = first["text"].split()
        second_words = second["text"].split()
        assert first_words[-50:] == second_words[:50]

    # Verify page boundaries are preserved.
    assert all(
        chunk["start_page"] == chunk["end_page"]
        for chunk in chunks
    )
    assert [chunk["start_page"] for chunk in chunks] == [1, 1, 2, 2]

    # Verify chunk IDs are unique.
    chunk_ids = [chunk["chunk_id"] for chunk in chunks]
    assert len(chunk_ids) == len(set(chunk_ids))



def test_chunk_pages_with_1100_words():
    sample_text = " ".join(
        f"word{i}" for i in range(1100)
    )

    pages = [
        {
            "page_number": 1,
            "text": sample_text,
        }
    ]

    chunks = chunk_pages(pages)

    # Starts: 0, 250, 500, 750, 1000
    assert len(chunks) == 5

    expected_sizes = [300, 300, 300, 300, 100]
    actual_sizes = [
        len(chunk["text"].split())
        for chunk in chunks
    ]

    assert actual_sizes == expected_sizes

    assert chunks[0]["start_word"] == 0
    assert chunks[1]["start_word"] == 250
    assert chunks[2]["start_word"] == 500
    assert chunks[3]["start_word"] == 750
    assert chunks[4]["start_word"] == 1000

    assert chunks[0]["start_page"] == 1
    assert chunks[0]["end_page"] == 1

    chunk_ids = [chunk["chunk_id"] for chunk in chunks]
    assert len(chunk_ids) == len(set(chunk_ids))


if __name__ == "__main__":
    test_chunk_pages_uses_size_and_overlap()
    test_chunk_pages_with_1100_words()

    print("All chunking tests passed!")
    print("Chunk size:", CHUNK_SIZE)
    print("Chunk overlap:", CHUNK_OVERLAP)
