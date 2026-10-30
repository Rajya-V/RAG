
from app.services.embedding_service import generate_embeddings
from app.services.vector_store_service import get_vector_collection

DOCUMENT_ID = "1e0966fa-6093-4621-be55-3b73ac16a36a"
QUERY = "What is this notification about?"

collection = get_vector_collection()
query_embedding = generate_embeddings([QUERY])[0]

results = collection.query(
    query_embeddings=[query_embedding],
    n_results=5,
    where={"document_id": DOCUMENT_ID},
    include=["documents", "metadatas", "distances"],
)

for i, chunk_id in enumerate(results["ids"][0]):
    print(f"\nResult {i + 1}")
    print("Distance:", round(results["distances"][0][i], 4))
    print("Filename:", results["metadatas"][0][i]["filename"])
    print("Pages:",
          results["metadatas"][0][i]["start_page"],
          "-",
          results["metadatas"][0][i]["end_page"])
    print("Text:", results["documents"][0][i][:300])
