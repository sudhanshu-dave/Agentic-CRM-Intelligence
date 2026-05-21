from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload

from app.core.errors import AppError
from app.core.responses import success_response
from app.database import get_db
from app.models import Email, EmailThread


router = APIRouter(prefix="/audit", tags=["Audit"])


def serialize_action(action):
    return {
        "id": action.id,
        "action_type": action.action_type,
        "agent_reasoning_log": action.agent_reasoning_log,
        "proposed_content": action.proposed_content,
        "is_approved": action.is_approved,
        "approved_by": action.approved_by,
        "executed_at": action.executed_at.isoformat() if action.executed_at else None,
        "created_at": action.created_at.isoformat() if action.created_at else None,
    }


def serialize_email_audit(email: Email):
    return {
        "id": email.id,
        "message_id": email.message_id,
        "sender": email.sender,
        "subject": email.subject,
        "body": email.body,
        "timestamp": email.timestamp.isoformat() if email.timestamp else None,
        "category": email.category,
        "urgency": email.urgency,
        "status": email.status,
        "requires_human": email.requires_human,
        "confidence": email.confidence,
        "sentiment_score": email.sentiment_score,
        "priority_score": email.priority_score,
        "raw_entities": email.raw_entities,
        "heuristic_flags": email.heuristic_flags,
        "thread": {
            "id": email.thread.id if email.thread else None,
            "thread_id": email.thread.thread_id if email.thread else None,
            "subject": email.thread.subject if email.thread else None,
            "status": email.thread.status if email.thread else None,
        },
        "actions": [serialize_action(action) for action in email.actions],
    }


@router.get("/email/{email_id}")
def get_email_audit(
    email_id: int,
    db: Session = Depends(get_db),
):
    email = (
        db.query(Email)
        .options(
            joinedload(Email.thread),
            joinedload(Email.actions),
        )
        .filter(Email.id == email_id)
        .first()
    )

    if not email:
        raise AppError(
            status_code=404,
            error_code="EMAIL_NOT_FOUND",
            message="No email found for this id.",
            details={"email_id": email_id},
        )

    return success_response(
        data=serialize_email_audit(email),
        message="Email audit trail retrieved successfully.",
    )


@router.get("/thread/{thread_id}")
def get_thread_audit(
    thread_id: str,
    db: Session = Depends(get_db),
):
    thread = (
        db.query(EmailThread)
        .options(
            joinedload(EmailThread.emails).joinedload(Email.actions),
        )
        .filter(EmailThread.thread_id == thread_id)
        .first()
    )

    if not thread:
        raise AppError(
            status_code=404,
            error_code="THREAD_NOT_FOUND",
            message="No thread found for this thread_id.",
            details={"thread_id": thread_id},
        )

    return success_response(
        data={
            "thread": {
                "id": thread.id,
                "thread_id": thread.thread_id,
                "subject": thread.subject,
                "sender_email": thread.sender_email,
                "first_seen_at": thread.first_seen_at.isoformat() if thread.first_seen_at else None,
                "last_updated_at": thread.last_updated_at.isoformat() if thread.last_updated_at else None,
                "status": thread.status,
                "assigned_to": thread.assigned_to,
            },
            "emails": [serialize_email_audit(email) for email in thread.emails],
        },
        message="Thread audit trail retrieved successfully.",
    )