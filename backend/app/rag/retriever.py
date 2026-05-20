from sqlalchemy.orm import Session

from app.models import KnowledgeChunk
from app.rag.embeddings import cosine_similarity, embed_text


def search_knowledge_base(
    db: Session,
    query: str,
    top_k: int = 3,
) -> list[dict]:
    query_embedding = embed_text(query)

    chunks = db.query(KnowledgeChunk).all()

    scored_chunks = []

    for chunk in chunks:
        score = cosine_similarity(query_embedding, chunk.embedding)

        scored_chunks.append(
            {
                "id": chunk.id,
                "source_doc": chunk.source_doc,
                "chunk_text": chunk.chunk_text,
                "similarity_score": round(float(score), 4),
            }
        )

    scored_chunks.sort(
        key=lambda item: item["similarity_score"],
        reverse=True,
    )

    return scored_chunks[:top_k]