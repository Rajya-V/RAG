
import time

from app.services.search_service import search_documents

QUERY = "What is the essential educational qualification for the Scientific/Technical Assistant-A post?"
TOP_K = 5
RUNS = 5

# Warm-up: load models and initialize services.
search_documents(query=QUERY, top_k=TOP_K)

times = []

for run in range(RUNS):
    start = time.perf_counter()
    results = search_documents(query=QUERY, top_k=TOP_K)
    elapsed = time.perf_counter() - start

    times.append(elapsed)
    print(
        f"Run {run + 1}: {elapsed:.3f}s | "
        f"Results: {len(results)}"
    )

print(f"\nAverage latency: {sum(times) / len(times):.3f}s")
print(f"Minimum latency: {min(times):.3f}s")
print(f"Maximum latency: {max(times):.3f}s")
