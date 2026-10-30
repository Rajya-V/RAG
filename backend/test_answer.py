
from app.services.answer_service import generate_answer


DOCUMENT_ID = "ddb7b68f-9e62-4ef4-b4ad-91ffb8c265e6"


def test_generate_answer():
    result = generate_answer(
        query="What is a primary key in DBMS?",
        top_k=3,
        document_id=DOCUMENT_ID,
    )

    assert result["answer"]
    assert len(result["sources"]) > 0

    print("\nGenerated answer:")
    print(result["answer"])

    print("\nSources:")
    for source in result["sources"]:
        print(
            f"- {source['filename']}, "
            f"pages {source['start_page']}-{source['end_page']}"
        )


if __name__ == "__main__":
    test_generate_answer()
