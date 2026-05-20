from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.core.responses import success_response
from app.database import get_db
from app.models import Contact, EmailThread


router = APIRouter(prefix="/threads", tags=["Threads"])


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


def serialize_email(email):
    return {
        "id": email.id,
        "message_id": email.message_id,
        "sender": email.sender,
        "subject": email.subject,
        "body": email.body,
        "timestamp": email.timestamp.isoformat() if email.timestamp else None,
        "sentiment_score": email.sentiment_score,
        "category": email.category,
        "urgency": email.urgency,
        "requires_human": email.requires_human,
        "confidence": email.confidence,
        "raw_entities": email.raw_entities,
        "status": email.status,
        "priority_score": email.priority_score,
        "heuristic_flags": email.heuristic_flags,
        "actions": [serialize_action(action) for action in email.actions],
    }


def serialize_thread(thread):
    return {
        "id": thread.id,
        "thread_id": thread.thread_id,
        "subject": thread.subject,
        "sender_email": thread.sender_email,
        "first_seen_at": thread.first_seen_at.isoformat() if thread.first_seen_at else None,
        "last_updated_at": thread.last_updated_at.isoformat() if thread.last_updated_at else None,
        "status": thread.status,
        "assigned_to": thread.assigned_to,
        "emails": [serialize_email(email) for email in thread.emails],
    }


@router.get("/{contact_email}")
def get_threads_for_contact(
    contact_email: str,
    db: Session = Depends(get_db),
):
    contact = db.query(Contact).filter(Contact.email == contact_email).first()

    if not contact:
        raise AppError(
            status_code=404,
            error_code="CONTACT_NOT_FOUND",
            message="No contact found for this email.",
            details={"contact_email": contact_email},
        )

    threads = (
        db.query(EmailThread)
        .filter(EmailThread.sender_email == contact.email)
        .order_by(EmailThread.last_updated_at.desc())
        .all()
    )

    return success_response(
        data={
            "contact": {
                "id": contact.id,
                "email": contact.email,
                "name": contact.name,
                "company": contact.company,
                "status": contact.status,
                "account_value": contact.account_value,
                "churn_risk_score": contact.churn_risk_score,
                "created_at": contact.created_at.isoformat() if contact.created_at else None,
                "last_contact_at": contact.last_contact_at.isoformat() if contact.last_contact_at else None,
            },
            "threads": [serialize_thread(thread) for thread in threads],
        },
        message="Thread history retrieved successfully.",
    )