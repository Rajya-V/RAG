
from app.services.search_service import search_documents


DOCUMENT_ID = "ddb7b68f-9e62-4ef4-b4ad-91ffb8c265e6"


def test_search_documents():
    results = search_documents(
        query="How do database tables establish relationships?",
        top_k=3,
        document_id=DOCUMENT_ID,
    )

    assert results, "Expected at least one relevant result."

    for result in results:
        assert result["text"]
        assert result["metadata"]["filename"]
        assert "start_page" in result["metadata"]
        assert "end_page" in result["metadata"]
        assert isinstance(result["distance"], float)
        assert result["distance"] <= 0.75

    print("Semantic search test passed!")
    print("Results returned:", len(results))

    for result in results:
        print(
            f"Pages {result['metadata']['start_page']}-"
            f"{result['metadata']['end_page']}"
        )
        print("Distance:", round(result["distance"], 4))
        print("Text preview:", result["text"][:150])
        print()


def test_search_filters_distant_chunks():
    results = search_documents(
        query="What is a primary key in DBMS?",
        top_k=3,
        document_id=DOCUMENT_ID,
    )

    assert results, "Expected at least one relevant result."

    for result in results:
        assert result["distance"] <= 0.95

    print("Retrieval threshold test passed!")
    print("Relevant results:", len(results))

def test_search_returns_no_results_when_collection_is_empty():
    from unittest.mock import patch

    with patch(
        "app.services.search_service.generate_embeddings",
        return_value=[[0.0] * 384],
    ), patch(
        "app.services.search_service.get_vector_collection"
    ) as mock_collection:
        mock_collection.return_value.count.return_value = 0

        results = search_documents(
            query="What is the company's office cafeteria menu?",
            top_k=3,
        )

    assert results == []


if __name__ == "__main__":
    test_search_documents()
    test_search_filters_distant_chunks()   
    test_search_returns_no_results_when_collection_is_empty()
                            