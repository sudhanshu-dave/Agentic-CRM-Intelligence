import re


def tokenize_text(text: str) -> list[str]:
    return re.findall(r"\S+", text)


def chunk_text(
    text: str,
    chunk_size: int = 420,
    overlap: int = 80,
) -> list[str]:
    """
    Chunk text into 300-500 token style segments with overlap.
    This keeps chunks small enough for LLM context injection.
    """
    tokens = tokenize_text(text)

    if not tokens:
        return []

    if chunk_size <= overlap:
        raise ValueError("chunk_size must be greater than overlap.")

    chunks = []
    start = 0

    while start < len(tokens):
        end = start + chunk_size
        chunk_tokens = tokens[start:end]
        chunks.append(" ".join(chunk_tokens))

        if end >= len(tokens):
            break

        start = end - overlap

    return chunks