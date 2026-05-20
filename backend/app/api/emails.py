from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, or_
from sqlalchemy.orm import Session, joinedload

from app.core.responses import success_response
from app.database import get_db
from app.models import Email


router = APIRouter(prefix="/emails", tags=["Emails"])


def serialize_email_for_list(email: Email) -> dict:
    return {
        "id": email.id,
        "message_id": email.message_id,
        "sender": email.sender,
        "subject": email.subject,
        "body_preview": email.body[:180] + "..." if len(email.body) > 180 else email.body,
        "timestamp": email.timestamp.isoformat() if email.timestamp else None,
        "category": email.category,
        "urgency": email.urgency,
        "status": email.status,
        "requires_human": email.requires_human,
        "confidence": email.confidence,
        "sentiment_score": email.sentiment_score,
        "priority_score": email.priority_score,
        "heuristic_flags": email.heuristic_flags,
        "thread": {
            "id": email.thread.id if email.thread else None,
            "thread_id": email.thread.thread_id if email.thread else None,
            "subject": email.thread.subject if email.thread else None,
            "status": email.thread.status if email.thread else None,
            "last_updated_at": (
                email.thread.last_updated_at.isoformat()
                if email.thread and email.thread.last_updated_at
                else None
            ),
        },
    }


@router.get("")
def list_emails(
    db: Session = Depends(get_db),
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    category: str | None = Query(default=None),
    urgency: str | None = Query(default=None),
    status: str | None = Query(default=None),
    requires_human: bool | None = Query(default=None),
    search: str | None = Query(default=None),
):
    query = db.query(Email).options(joinedload(Email.thread))

    if category:
        query = query.filter(Email.category == category)

    if urgency:
        query = query.filter(Email.urgency == urgency)

    if status:
        query = query.filter(Email.status == status)

    if requires_human is not None:
        query = query.filter(Email.requires_human.is_(requires_human))

    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            or_(
                Email.subject.ilike(search_pattern),
                Email.body.ilike(search_pattern),
                Email.sender.ilike(search_pattern),
                Email.message_id.ilike(search_pattern),
            )
        )

    total = query.with_entities(func.count(Email.id)).scalar() or 0

    emails = (
        query.order_by(Email.timestamp.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return success_response(
        data={
            "items": [serialize_email_for_list(email) for email in emails],
            "pagination": {
                "total": total,
                "limit": limit,
                "offset": offset,
                "returned": len(emails),
            },
            "filters": {
                "category": category,
                "urgency": urgency,
                "status": status,
                "requires_human": requires_human,
                "search": search,
            },
        },
        message="Emails retrieved successfully.",
    )