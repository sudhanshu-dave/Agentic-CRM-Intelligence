from sqlalchemy import func
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends

from app.core.responses import success_response
from app.database import get_db
from app.models import Email, EmailThread, Contact


router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


def count_emails_by_status(db: Session, status_value: str) -> int:
    return db.query(func.count(Email.id)).filter(Email.status == status_value).scalar() or 0


def count_emails_by_category(db: Session, category_value: str) -> int:
    return db.query(func.count(Email.id)).filter(Email.category == category_value).scalar() or 0


def count_emails_by_urgency(db: Session, urgency_value: str) -> int:
    return db.query(func.count(Email.id)).filter(Email.urgency == urgency_value).scalar() or 0


@router.get("/stats")
def get_dashboard_stats(db: Session = Depends(get_db)):
    total_emails = db.query(func.count(Email.id)).scalar() or 0
    total_threads = db.query(func.count(EmailThread.id)).scalar() or 0
    total_contacts = db.query(func.count(Contact.id)).scalar() or 0

    pending_count = (
        db.query(func.count(Email.id))
        .filter(Email.status.in_(["Received", "Processing"]))
        .scalar()
        or 0
    )

    replied_count = count_emails_by_status(db, "Replied")
    escalated_count = count_emails_by_status(db, "Escalated")
    spam_filtered_count = count_emails_by_category(db, "Spam")
    critical_count = count_emails_by_urgency(db, "Critical")
    needs_human_count = (
        db.query(func.count(Email.id))
        .filter(Email.requires_human.is_(True))
        .scalar()
        or 0
    )

    category_breakdown = (
        db.query(Email.category, func.count(Email.id))
        .group_by(Email.category)
        .order_by(func.count(Email.id).desc())
        .all()
    )

    urgency_breakdown = (
        db.query(Email.urgency, func.count(Email.id))
        .group_by(Email.urgency)
        .order_by(func.count(Email.id).desc())
        .all()
    )

    latest_emails = (
        db.query(Email)
        .order_by(Email.timestamp.desc())
        .limit(10)
        .all()
    )

    return success_response(
        data={
            "summary": {
                "total_emails": total_emails,
                "total_threads": total_threads,
                "total_contacts": total_contacts,
                "pending": pending_count,
                "replied": replied_count,
                "escalated": escalated_count,
                "critical": critical_count,
                "spam_filtered": spam_filtered_count,
                "needs_human": needs_human_count,
            },
            "category_breakdown": [
                {"category": category, "count": count}
                for category, count in category_breakdown
            ],
            "urgency_breakdown": [
                {"urgency": urgency, "count": count}
                for urgency, count in urgency_breakdown
            ],
            "latest_emails": [
                {
                    "id": email.id,
                    "message_id": email.message_id,
                    "sender": email.sender,
                    "subject": email.subject,
                    "timestamp": email.timestamp.isoformat() if email.timestamp else None,
                    "category": email.category,
                    "urgency": email.urgency,
                    "status": email.status,
                    "requires_human": email.requires_human,
                    "priority_score": email.priority_score,
                }
                for email in latest_emails
            ],
        },
        message="Dashboard stats retrieved successfully.",
    )