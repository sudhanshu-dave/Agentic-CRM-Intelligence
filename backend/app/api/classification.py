from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.responses import success_response
from app.database import get_db
from app.services.classification_service import classify_batch, classify_email


router = APIRouter(prefix="/classify", tags=["Classification"])


@router.post("/batch/run")
def classify_unprocessed_batch(
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    result = classify_batch(
        db=db,
        limit=limit,
    )

    return success_response(
        data=result,
        message="Batch classification completed successfully.",
    )


@router.post("/{email_id}")
def classify_single_email(
    email_id: int,
    db: Session = Depends(get_db),
):
    result = classify_email(
        db=db,
        email_id=email_id,
    )

    return success_response(
        data=result,
        message="Email classified successfully.",
    )