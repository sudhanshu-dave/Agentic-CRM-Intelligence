from fastapi import APIRouter

from app.core.responses import success_response

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("")
def health_check():
    return success_response(
        data={
            "status": "ok",
            "service": "Agentic CRM Intelligence Platform",
        }
    )