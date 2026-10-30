
import statistics
import time

from app.services.search_service import search_documents


TOP_K = 3

# Initial evaluation set.
# relevant_terms are provisional labels: a result counts as relevant
# when at least one listed phrase appears in its retrieved text.
# Review these labels against the source documents as the dataset grows.
EVALUATION_CASES = [
    {
        "name": "NIC educational qualification",
        "query": "What is the essential educational qualification for Scientific/Technical Assistant-A?",
        "document_id": "1e0966fa-6093-4621-be55-3b73ac16a36a",
        "relevant_terms": [
            "essential educational qualification",
            "m.sc.",
            "b.tech.",
            "computer sciences",
        ],
    },
    {
        "name": "NIC valid GATE score",
        "query": "Which GATE papers and years are accepted for this recruitment?",
        "document_id": "1e0966fa-6093-4621-be55-3b73ac16a36a",
        "relevant_terms": [
    "gate2024/2025/2026",
    "computer sciences and information technology",
    "electronics and communication engineering",
    "data science and artificial intelligence",
],
    },
    {
        "name": "NIC experience requirement",
        "query": "Is previous work experience required for the advertised post?",
        "document_id": "1e0966fa-6093-4621-be55-3b73ac16a36a",
        "relevant_terms": [
            "no experience required",
        ],
    },
    {
        "name": "DBMS table relationships",
        "query": "How do database tables establish relationships?",
        "document_id": "ddb7b68f-9e62-4ef4-b4ad-91ffb8c265e6",
        "relevant_terms": [
            "foreign key",
            "primary key",
            "relationship",
        ],
    },
    {
        "name": "DBMS primary key",
        "query": "What is a primary key in DBMS?",
        "document_id": "ddb7b68f-9e62-4ef4-b4ad-91ffb8c265e6",
        "relevant_terms": [
            "primary key",
            "unique",
            "null",
        ],
    },
]


def is_relevant(result: dict, relevant_terms: list[str]) -> bool:
    """Apply the initial phrase-based relevance labels."""
    text = result.get("text", "").lower()
    return any(term.lower() in text for term in relevant_terms)


def evaluate_case(case: dict) -> dict:
    start = time.perf_counter()

    results = search_documents(
        query=case["query"],
        top_k=TOP_K,
        document_id=case["document_id"],
    )

    latency = time.perf_counter() - start

    relevant_ranks = [
        rank
        for rank, result in enumerate(results, start=1)
        if is_relevant(result, case["relevant_terms"])
    ]

    hit = bool(relevant_ranks)
    reciprocal_rank = 1 / relevant_ranks[0] if hit else 0.0

    print(f"\nQuestion: {case['name']}")
    print(f"Query: {case['query']}")
    print(f"Latency: {latency:.3f}s")
    print(f"Relevant result in top {TOP_K}: {'YES' if hit else 'NO'}")

    for rank, result in enumerate(results, start=1):
        relevant = is_relevant(result, case["relevant_terms"])
        metadata = result.get("metadata") or {}

        print(
            f"  Rank {rank} | "
            f"Relevant: {relevant} | "
            f"File: {metadata.get('filename', 'Unknown')} | "
            f"Pages: {metadata.get('start_page', '?')}-"
            f"{metadata.get('end_page', '?')}"
        )

    if not hit:
        print(
            "  Review needed: inspect the retrieved chunks and "
            "adjust the relevance labels if necessary."
        )

    return {
        "hit": int(hit),
        "reciprocal_rank": reciprocal_rank,
        "latency": latency,
    }


def main():
    print("=" * 60)
    print("ENTERPRISE KNOWLEDGE COPILOT - RETRIEVAL EVALUATION")
    print("=" * 60)
    print(f"Questions: {len(EVALUATION_CASES)}")
    print(f"Top K: {TOP_K}")

    metrics = [
        evaluate_case(case)
        for case in EVALUATION_CASES
    ]

    recall_at_k = statistics.mean(item["hit"] for item in metrics)
    mrr = statistics.mean(
        item["reciprocal_rank"] for item in metrics
    )
    average_latency = statistics.mean(
        item["latency"] for item in metrics
    )

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Recall@{TOP_K}: {recall_at_k:.2%}")
    print(f"Hit rate@{TOP_K}: {recall_at_k:.2%}")
    print(f"MRR: {mrr:.4f}")
    print(f"Average latency: {average_latency:.3f}s")
    print(
        "\nNote: Metrics are provisional until the relevance labels "
        "are manually verified against the source documents."
    )


if __name__ == "__main__":
    main()
