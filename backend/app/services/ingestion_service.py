import re
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models import Contact, Email, EmailThread
from app.schemas.email import EmailIngestRequest
from app.services.heuristic_service import normalize_text, run_heuristic_triage


def extract_name_from_email(email: str) -> str:
    local_part = email.split("@", 1)[0]
    local_part = re.sub(r"[._-]+", " ", local_part)
    return local_part.title()


def extract_company_from_email(email: str) -> str | None:
    if "@" not in email:
        return None

    domain = email.split("@", 1)[1].lower()
    domain_main = domain.split(".")[0]

    generic_domains = {
        "gmail",
        "yahoo",
        "hotmail",
        "outlook",
        "freemail",
        "mit",
    }

    if domain_main in generic_domains:
        return None

    return domain_main.replace("-", " ").title()


def truncate_body_if_needed(body: str, limit: int = 10_000) -> str:
    if len(body) <= limit:
        return body

    return body[:limit] + "\n\n[TRUNCATED_FOR_LLM_PROCESSING]"


def ensure_timezone_aware(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def get_or_create_contact(
    db: Session,
    sender: str,
    timestamp: datetime,
) -> Contact:
    contact = db.query(Contact).filter(Contact.email == sender).first()

    if contact:
        contact.last_contact_at = timestamp
        return contact

    contact = Contact(
        email=sender,
        name=extract_name_from_email(sender),
        company=extract_company_from_email(sender),
        status="Active",
        account_value=0.0,
        churn_risk_score=0.0,
        created_at=datetime.now(timezone.utc),
        last_contact_at=timestamp,
    )

    db.add(contact)
    db.flush()

    return contact


def get_or_create_thread(
    db: Session,
    payload: EmailIngestRequest,
    contact: Contact,
    timestamp: datetime,
) -> EmailThread:
    thread = db.query(EmailThread).filter(
        EmailThread.thread_id == payload.thread_id
    ).first()

    clean_subject = normalize_text(payload.subject)

    if thread:
        if timestamp < thread.first_seen_at:
            thread.first_seen_at = timestamp

        if timestamp > thread.last_updated_at:
            thread.last_updated_at = timestamp
            thread.subject = clean_subject or thread.subject

        return thread

    thread = EmailThread(
        thread_id=payload.thread_id,
        subject=clean_subject,
        sender_email=contact.email,
        first_seen_at=timestamp,
        last_updated_at=timestamp,
        status="Open",
        assigned_to=None,
    )

    db.add(thread)
    db.flush()

    return thread


def ingest_email(
    db: Session,
    payload: EmailIngestRequest,
) -> dict[str, Any]:
    existing_email = db.query(Email).filter(
        Email.message_id == payload.message_id
    ).first()

    if existing_email:
        raise AppError(
            status_code=409,
            error_code="DUPLICATE_MESSAGE",
            message="Email with this message_id has already been ingested.",
            details={
                "message_id": payload.message_id,
                "existing_email_id": existing_email.id,
            },
        )

    timestamp = ensure_timezone_aware(payload.timestamp)

    clean_subject = normalize_text(payload.subject)
    clean_body = normalize_text(payload.body)
    stored_body = truncate_body_if_needed(clean_body)

    heuristic = run_heuristic_triage(
        sender=str(payload.sender),
        subject=clean_subject,
        body=clean_body,
    )

    contact = get_or_create_contact(
        db=db,
        sender=str(payload.sender),
        timestamp=timestamp,
    )

    thread = get_or_create_thread(
        db=db,
        payload=payload,
        contact=contact,
        timestamp=timestamp,
    )

    if heuristic.status == "Escalated":
        thread.status = "Escalated"

    email = Email(
        thread_db_id=thread.id,
        message_id=payload.message_id,
        sender=str(payload.sender),
        subject=clean_subject,
        body=stored_body,
        timestamp=timestamp,
        sentiment_score=None,
        category=heuristic.category,
        urgency=heuristic.urgency,
        requires_human=heuristic.requires_human,
        confidence=None,
        raw_entities={},
        status=heuristic.status,
        priority_score=heuristic.priority_score,
        heuristic_flags=heuristic.flags,
    )

    db.add(email)
    db.commit()
    db.refresh(email)

    return {
        "job_id": f"job_{email.message_id}",
        "email_id": email.id,
        "message_id": email.message_id,
        "thread_id": thread.thread_id,
        "status": email.status,
        "category": email.category,
        "urgency": email.urgency,
        "priority_score": email.priority_score,
        "requires_human": email.requires_human,
        "heuristic_flags": email.heuristic_flags,
    }


def get_email_processing_status(
    db: Session,
    job_id: str,
) -> dict[str, Any]:
    if not job_id.startswith("job_"):
        raise AppError(
            status_code=400,
            error_code="INVALID_JOB_ID",
            message="Invalid job_id format.",
            details={"job_id": job_id},
        )

    message_id = job_id.replace("job_", "", 1)

    email = db.query(Email).filter(Email.message_id == message_id).first()

    if not email:
        raise AppError(
            status_code=404,
            error_code="JOB_NOT_FOUND",
            message="No email processing job found for this job_id.",
            details={"job_id": job_id},
        )

    return {
        "job_id": job_id,
        "email_id": email.id,
        "message_id": email.message_id,
        "processing_status": email.status,
        "category": email.category,
        "urgency": email.urgency,
        "requires_human": email.requires_human,
    }