from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.responses import success_response
from app.database import get_db
from app.schemas.email import EmailIngestRequest
from app.services.ingestion_service import (
    get_email_processing_status,
    ingest_email,
)

router = APIRouter(tags=["Email Ingestion"])


@router.post("/api/ingest", status_code=status.HTTP_201_CREATED)
def ingest_email_endpoint(
    payload: EmailIngestRequest,
    db: Session = Depends(get_db),
):
    result = ingest_email(db=db, payload=payload)

    return success_response(
        data=result,
        message="Email ingested successfully.",
    )


@router.get("/api/status/{job_id}")
def get_processing_status_endpoint(
    job_id: str,
    db: Session = Depends(get_db),
):
    result = get_email_processing_status(db=db, job_id=job_id)

    return success_response(
        data=result,
        message="Email processing status retrieved successfully.",
    )