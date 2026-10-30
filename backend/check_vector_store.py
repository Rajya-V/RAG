
from app.services.vector_store_service import get_vector_collection

collection = get_vector_collection()

print("Total chunks in database:", collection.count())

document_id = "1e0966fa-6093-4621-be55-3b73ac16a36a"

results = collection.get(
    where={"document_id": document_id},
    include=["documents", "metadatas"],
)

print("Chunks for notification:", len(results["ids"]))

for i, chunk_id in enumerate(results["ids"][:3]):
    print("\nChunk ID:", chunk_id)
    print("Metadata:", results["metadatas"][i])
    print("Text preview:", results["documents"][i][:200])
