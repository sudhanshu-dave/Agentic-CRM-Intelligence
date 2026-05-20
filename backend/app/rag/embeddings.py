import hashlib
import math
import re


EMBEDDING_DIMENSION = 384


def normalize_text(text: str) -> str:
    return text.lower().strip()


def tokenize_for_embedding(text: str) -> list[str]:
    normalized = normalize_text(text)
    return re.findall(r"[a-zA-Z0-9_.$#/-]+", normalized)


def stable_hash(value: str) -> int:
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()
    return int(digest, 16)


def embed_text(text: str, dimension: int = EMBEDDING_DIMENSION) -> list[float]:
    """
    Local deterministic embedding fallback using feature hashing.

    This is intentionally dependency-free for the take-home MVP.
    In production, this can be replaced with OpenAI, Cohere,
    sentence-transformers, or pgvector-compatible embeddings.
    """
    tokens = tokenize_for_embedding(text)

    vector = [0.0] * dimension

    for token in tokens:
        hashed = stable_hash(token)
        index = hashed % dimension
        sign = 1.0 if (hashed // dimension) % 2 == 0 else -1.0
        vector[index] += sign

    norm = math.sqrt(sum(value * value for value in vector))

    if norm == 0:
        return vector

    return [value / norm for value in vector]


def cosine_similarity(vector_a: list[float], vector_b: list[float]) -> float:
    if not vector_a or not vector_b:
        return 0.0

    length = min(len(vector_a), len(vector_b))

    dot_product = sum(vector_a[i] * vector_b[i] for i in range(length))
    norm_a = math.sqrt(sum(vector_a[i] * vector_a[i] for i in range(length)))
    norm_b = math.sqrt(sum(vector_b[i] * vector_b[i] for i in range(length)))

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return dot_product / (norm_a * norm_b)