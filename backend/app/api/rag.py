from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.core.responses import success_response
from app.database import get_db
from app.models import KnowledgeChunk
from app.rag.retriever import search_knowledge_base


router = APIRouter(prefix="/rag", tags=["RAG"])


@router.get("/search")
def rag_search(
    q: str = Query(..., min_length=1, description="Search query for internal knowledge base."),
    top_k: int = Query(default=3, ge=1, le=10),
    db: Session = Depends(get_db),
):
    chunk_count = db.query(KnowledgeChunk).count()

    if chunk_count == 0:
        raise AppError(
            status_code=400,
            error_code="KNOWLEDGE_BASE_EMPTY",
            message="Knowledge base has not been seeded yet.",
            details={
                "hint": "Run: python backend/scripts/seed_kb.py --reset"
            },
        )

    results = search_knowledge_base(
        db=db,
        query=q,
        top_k=top_k,
    )

    return success_response(
        data={
            "query": q,
            "top_k": top_k,
            "results": results,
        },
        message="RAG search completed successfully.",
    )