
#embedding_service.py
from functools import lru_cache

from sentence_transformers import SentenceTransformer


MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


@lru_cache(maxsize=1)
def get_embedding_model() -> SentenceTransformer:
    """
    Load the embedding model once and reuse it.
    The model runs locally on the CPU by default.
    """
    return SentenceTransformer(MODEL_NAME, device="cpu")


def generate_embeddings(texts: list[str]) -> list[list[float]]:
    """
    Convert text strings into embedding vectors.

    Returns one 384-dimensional vector per input text.
    """
    if not texts:
        return []

    if any(not text.strip() for text in texts):
        raise ValueError("Input texts must not contain empty strings.")

    model = get_embedding_model()

    embeddings = model.encode(
        texts,
        normalize_embeddings=True,
        convert_to_numpy=True,
        show_progress_bar=False,
    )

    return embeddings.tolist()
