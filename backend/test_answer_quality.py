
from app.services.answer_service import generate_answer

DOCUMENT_ID = "ac060226-2266-46cf-a54c-1ea1927163ef"


def test_eligibility_answer_quality():
    result = generate_answer(
        query=(
            "What educational qualification is required for "
            "CS, EC, and DA disciplines? Which GATE paper codes "
            "and years are accepted? Does the notification specify "
            "minimum marks?"
        ),
        top_k=5,
        document_id=DOCUMENT_ID,
    )

    answer = result["answer"].lower()

    # All three GATE paper codes must appear.
    assert "cs" in answer
    assert "ec" in answer
    assert "da" in answer

    # The shared qualification list should be represented.
    assert "m.sc." in answer or "msc" in answer
    assert "b.e." in answer or "be" in answer
    assert "b.tech." in answer or "btech" in answer

    # Accepted GATE years should be mentioned.
    assert "2024" in answer
    assert "2025" in answer
    assert "2026" in answer

    # The answer must include source information.
    assert result["sources"]
    assert any(
        source["filename"] == "NIC-STA-Notification-2026.pdf"
        for source in result["sources"]
    )

def test_unanswerable_question_does_not_invent_facts():
    result = generate_answer(
        query="What is the cafeteria menu at the National Informatics Centre?",
        top_k=3,
        document_id=DOCUMENT_ID,
    )

    answer = result["answer"].lower()

    # The answer should acknowledge that the information is missing.
    assert any(
        phrase in answer
        for phrase in [
            "does not contain",
            "couldn't find",
            "could not find",
            "not contain any information",
            "not mentioned",
            "no information",
        ]
    )

