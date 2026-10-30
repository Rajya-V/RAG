
from app.services.search_service import search_documents


DOCUMENT_ID = "ac060226-2266-46cf-a54c-1ea1927163ef"

QUERY = (
    "Does the Scientific Technical Assistant A position require prior work experience?"
)


def main():
    results = search_documents(
        query=QUERY,
        top_k=10,
        document_id=DOCUMENT_ID,
    )

    if not results:
        print("No matching results found.")
        return

    for rank, result in enumerate(results, start=1):
        metadata = result["metadata"]

        print(f"\nRank: {rank}")
        print(f"Distance: {result['distance']}")
        print(f"Filename: {metadata.get('filename', 'Unknown')}")
        print(
            f"Pages: {metadata.get('start_page', '?')}"
            f"-{metadata.get('end_page', '?')}"
        )
        print(f"Text: {result['text']}")
        print("-" * 60)


if __name__ == "__main__":
    main()
