
import re

from rank_bm25 import BM25Okapi

from app.services.embedding_service import generate_embeddings
from app.services.vector_store_service import get_vector_collection


RRF_K = 60


def tokenize(text: str) -> list[str]:
    """Normalize text for BM25 keyword retrieval."""
    stop_words = {
        "a", "an", "and", "are", "as", "at", "be", "by",
        "does", "do", "did", "for", "from", "has", "have",
        "how", "i", "in", "is", "it", "of", "on", "or",
        "the", "this", "to", "was", "were", "what", "when",
        "where", "which", "who", "why", "will", "with",
    }

    tokens = re.findall(r"\b[a-zA-Z0-9]+\b", text.lower())
    normalized = []

    for token in tokens:
        if token in stop_words:
            continue

        if len(token) > 5 and token.endswith("ing"):
            token = token[:-3]
        elif len(token) > 4 and token.endswith("ed"):
            token = token[:-2]
        elif len(token) > 4 and token.endswith("es"):
            token = token[:-2]
        elif len(token) > 3 and token.endswith("s"):
            token = token[:-1]

        normalized.append(token)

    return normalized


def search_documents(
    query: str,
    top_k: int = 3,
    document_id: str | None = None,
    document_ids: list[str] | None = None,
) -> list[dict]:
    """
    Retrieve document chunks using semantic search and BM25,
    combine rankings with weighted Reciprocal Rank Fusion,
    and return relevant results from the selected documents.
    """

    if not query or not query.strip():
        raise ValueError("Search query must not be empty.")

    if top_k < 1:
        raise ValueError("top_k must be at least 1.")

    # 1. Normalize selected document IDs.
    selected_ids = list(
        dict.fromkeys(
            str(doc_id).strip()
            for doc_id in (document_ids or [])
            if doc_id and str(doc_id).strip()
        )
    )

    if document_id:
        document_id = str(document_id).strip()

        if document_id and document_id not in selected_ids:
            selected_ids.append(document_id)

    document_filter = None

    if len(selected_ids) == 1:
        document_filter = {"document_id": selected_ids[0]}
    elif len(selected_ids) > 1:
        document_filter = {
            "document_id": {"$in": selected_ids}
        }

    collection = get_vector_collection()

    # 2. Diagnose selected document IDs and stored chunks.
    print("\n--- DOCUMENT ID CHECK ---")
    print("Query:", query)
    print("Selected IDs:", selected_ids or "All documents")

    for doc_id in selected_ids:
        stored = collection.get(
            where={"document_id": doc_id},
            include=["metadatas"],
        )

        metadatas = stored.get("metadatas") or []
        filenames = sorted({
            metadata.get("filename", "Unknown")
            for metadata in metadatas
            if metadata
        })

        print(
            f"ID={doc_id} | "
            f"Chunks={len(stored.get('ids', []))} | "
            f"Files={filenames}"
        )

    # Count all chunks matching the filter.
    if document_filter:
        matching = collection.get(
            where=document_filter,
            include=[],
        )
        total_chunks = len(matching.get("ids", []))
    else:
        total_chunks = collection.count()

    print("Combined matching chunks:", total_chunks)
    print("--- END DOCUMENT ID CHECK ---\n")

    if total_chunks == 0:
        return []

    # 3. Semantic retrieval.
    query_embedding = generate_embeddings([query])[0]

    semantic_results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(max(top_k * 10, 30), total_chunks),
        where=document_filter,
        include=["documents", "metadatas", "distances"],
    )

    semantic_ids = semantic_results.get("ids", [[]])[0]
    semantic_documents = semantic_results.get("documents", [[]])[0]
    semantic_metadatas = semantic_results.get("metadatas", [[]])[0]
    semantic_distances = semantic_results.get("distances", [[]])[0]

    candidates = {}
    semantic_rank = {}

    print("--- SEMANTIC RETRIEVAL DEBUG ---")

    for rank, chunk_id in enumerate(semantic_ids, start=1):
        distance = float(semantic_distances[rank - 1])
        metadata = semantic_metadatas[rank - 1] or {}

        print(
            f"Rank={rank} | "
            f"File={metadata.get('filename', 'Unknown')} | "
            f"Document ID={metadata.get('document_id')} | "
            f"Page={metadata.get('start_page')} | "
            f"Distance={distance:.4f}"
        )

        # Keep semantic candidates regardless of distance.
        # RRF uses their relative rank; BM25 supplies a second signal.
        candidates[chunk_id] = {
            "chunk_id": chunk_id,
            "text": semantic_documents[rank - 1] or "",
            "metadata": metadata,
            "distance": distance,
        }

        semantic_rank[chunk_id] = rank

    print("--- END SEMANTIC RETRIEVAL DEBUG ---\n")

    # 4. Retrieve all chunks matching the selected document filter
    # for BM25. Pagination avoids depending on one large get() call.
    page_size = 500
    offset = 0

    keyword_ids = []
    keyword_documents = []
    keyword_metadatas = []

    while offset < total_chunks:
        batch = collection.get(
            where=document_filter,
            limit=min(page_size, total_chunks - offset),
            offset=offset,
            include=["documents", "metadatas"],
        )

        batch_ids = batch.get("ids", [])

        if not batch_ids:
            break

        batch_documents = batch.get("documents") or []
        batch_metadatas = batch.get("metadatas") or []

        for index, chunk_id in enumerate(batch_ids):
            keyword_ids.append(chunk_id)
            keyword_documents.append(batch_documents[index] or "")
            keyword_metadatas.append(batch_metadatas[index] or {})

        offset += len(batch_ids)

    # 5. BM25 keyword retrieval.
    query_tokens = tokenize(query)

    print("--- BM25 DEBUG ---")
    print("Query tokens:", query_tokens)
    print("Chunks loaded:", len(keyword_documents))

    if query_tokens and keyword_documents:
        tokenized_documents = [
            tokenize(document)
            for document in keyword_documents
        ]

        valid_indices = [
            index
            for index, tokens in enumerate(tokenized_documents)
            if tokens
        ]

        if valid_indices:
            bm25_documents = [
                tokenized_documents[index]
                for index in valid_indices
            ]

            bm25 = BM25Okapi(bm25_documents)
            scores = bm25.get_scores(query_tokens)

            ranked_indices = sorted(
                range(len(valid_indices)),
                key=lambda index: float(scores[index]),
                reverse=True,
            )

            keyword_rank = 0

            for ranked_index in ranked_indices:
                original_index = valid_indices[ranked_index]
                score = float(scores[ranked_index])

                if score <= 0:
                    continue

                keyword_rank += 1
                chunk_id = keyword_ids[original_index]
                text = keyword_documents[original_index]
                metadata = keyword_metadatas[original_index]

                print(
                    f"Rank={keyword_rank} | "
                    f"Score={score:.4f} | "
                    f"File={metadata.get('filename')} | "
                    f"Document ID={metadata.get('document_id')} | "
                    f"Page={metadata.get('start_page')}"
                )

                if chunk_id not in candidates:
                    candidates[chunk_id] = {
                        "chunk_id": chunk_id,
                        "text": text,
                        "metadata": metadata,
                        "distance": None,
                    }

                candidates[chunk_id]["keyword_rank"] = keyword_rank

    print("--- END BM25 DEBUG ---\n")

    # 6. Weighted Reciprocal Rank Fusion.
    rrf_scores = {}

    for chunk_id, item in candidates.items():
        score = 0.0

        if chunk_id in semantic_rank:
            score += 1.0 / (
                RRF_K + semantic_rank[chunk_id]
            )

        if "keyword_rank" in item:
            score += 1.5 / (
                RRF_K + item["keyword_rank"]
            )

        rrf_scores[chunk_id] = score

    ranked_ids = sorted(
        rrf_scores,
        key=lambda chunk_id: rrf_scores[chunk_id],
        reverse=True,
    )

    print("--- RRF DEBUG ---")

    for rank, chunk_id in enumerate(ranked_ids[:15], start=1):
        item = candidates[chunk_id]
        metadata = item.get("metadata") or {}

        print(
            f"Rank={rank} | "
            f"RRF={rrf_scores[chunk_id]:.5f} | "
            f"Semantic rank={semantic_rank.get(chunk_id)} | "
            f"BM25 rank={item.get('keyword_rank')} | "
            f"File={metadata.get('filename')} | "
            f"Document ID={metadata.get('document_id')} | "
            f"Page={metadata.get('start_page')}"
        )

    # 7. Select results.
    # For multi-PDF queries, give each selected document a chance
    # to contribute its highest-ranked available chunk.
    selected_chunk_ids = []
    selected_set = set()

    if len(selected_ids) > 1:
        for doc_id in selected_ids:
            for chunk_id in ranked_ids:
                metadata = candidates[chunk_id].get("metadata") or {}

                if metadata.get("document_id") == doc_id:
                    selected_chunk_ids.append(chunk_id)
                    selected_set.add(chunk_id)
                    break

    # Fill remaining slots with the overall highest-ranked chunks.
    result_limit = max(top_k, len(selected_chunk_ids))

    for chunk_id in ranked_ids:
        if chunk_id not in selected_set:
            selected_chunk_ids.append(chunk_id)
            selected_set.add(chunk_id)

        if len(selected_chunk_ids) >= result_limit:
            break

    print("--- FINAL RAG RETRIEVAL ---")

    for chunk_id in selected_chunk_ids:
        metadata = candidates[chunk_id].get("metadata") or {}

        print(
            f"File={metadata.get('filename')} | "
            f"Document ID={metadata.get('document_id')} | "
            f"Page={metadata.get('start_page')}"
        )

    print("--- END FINAL RAG RETRIEVAL ---\n")

    return [
        {
            **candidates[chunk_id],
            "score": rrf_scores[chunk_id],
        }
        for chunk_id in selected_chunk_ids
    ]
