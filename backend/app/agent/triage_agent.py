from typing import Any

from sqlalchemy.orm import Session

from app.agent.tools import (
    check_account_status_tool,
    create_action_record_tool,
    draft_reply_tool,
    get_contact_profile_tool,
    get_thread_history_tool,
    search_knowledge_base_tool,
)
from app.core.errors import AppError
from app.models import Email
from app.services.classification_service import build_rag_query, classify_email


def add_trace(
    trace: list[dict[str, Any]],
    thought: str,
    action: str,
    observation: Any,
    next_step: str,
) -> None:
    trace.append(
        {
            "thought": thought,
            "action": action,
            "observation": observation,
            "next": next_step,
        }
    )


def should_never_auto_reply(email: Email) -> tuple[bool, str | None]:
    flags = email.heuristic_flags or {}

    if email.category == "Spam" or flags.get("spam_flag"):
        return True, "Spam must not receive an auto-reply."

    if flags.get("security_flag"):
        return True, "Security threats must not receive an auto-reply."

    if email.urgency == "Critical":
        return True, "Critical urgency requires human review."

    if email.category == "Legal" or flags.get("legal_flag"):
        return True, "Legal issues require human review."

    return False, None


def decide_rag_query(email: Email) -> str:
    return build_rag_query(email)


def summarize_thread(thread_history: dict[str, Any]) -> dict[str, Any]:
    emails = thread_history.get("emails", [])

    return {
        "thread_id": thread_history.get("thread_id"),
        "message_count": len(emails),
        "first_message": emails[0]["timestamp"] if emails else None,
        "latest_message": emails[-1]["timestamp"] if emails else None,
        "subjects": [item["subject"] for item in emails],
    }


def determine_action_type(email: Email) -> str:
    flags = email.heuristic_flags or {}

    if flags.get("security_flag"):
        return "Security-Escalation"

    if email.category == "Legal" or flags.get("legal_flag"):
        return "Legal-Flag"

    if email.category == "Spam":
        return "Ignored"

    if email.requires_human:
        return "Escalate"

    return "Draft-Reply"


def run_triage_agent_dry_run(
    db: Session,
    email_id: int,
    persist: bool = True,
) -> dict[str, Any]:
    email = db.query(Email).filter(Email.id == email_id).first()

    if not email:
        raise AppError(
            status_code=404,
            error_code="EMAIL_NOT_FOUND",
            message="No email found for this id.",
            details={"email_id": email_id},
        )

    reasoning_trace: list[dict[str, Any]] = []

    classification_result = classify_email(db=db, email_id=email.id)
    db.refresh(email)

    add_trace(
        reasoning_trace,
        thought="Start by classifying the email with current thread and RAG context.",
        action="classify_email",
        observation={
            "category": classification_result["classification"]["category"],
            "urgency": classification_result["classification"]["urgency"],
            "requires_human": classification_result["classification"]["requires_human"],
            "confidence": classification_result["classification"]["confidence"],
            "policy_refs": classification_result["classification"]["policy_refs"],
        },
        next_step="Retrieve full thread history before deciding final action.",
    )

    thread_history = get_thread_history_tool(email)

    add_trace(
        reasoning_trace,
        thought="The agent must inspect the full conversation thread, not only the latest email.",
        action="get_thread_history",
        observation=summarize_thread(thread_history),
        next_step="Search the internal knowledge base for relevant policy context.",
    )

    rag_query = decide_rag_query(email)
    rag_results = search_knowledge_base_tool(
        db=db,
        query=rag_query,
        top_k=3,
    )

    add_trace(
        reasoning_trace,
        thought="Policy-grounded context is required before drafting or escalating.",
        action="search_knowledge_base",
        observation={
            "query": rag_query,
            "policy_refs": [item["source_doc"] for item in rag_results],
            "top_score": rag_results[0]["similarity_score"] if rag_results else None,
        },
        next_step="Retrieve CRM contact profile.",
    )

    contact_profile = get_contact_profile_tool(db=db, email_address=email.sender)

    add_trace(
        reasoning_trace,
        thought="Customer profile helps determine priority, VIP status, and churn risk.",
        action="get_contact_profile",
        observation=contact_profile,
        next_step="Check account and billing/SLA status.",
    )

    account_status = check_account_status_tool(email.sender)

    add_trace(
        reasoning_trace,
        thought="Account status is required for SLA, renewal, billing, and routing decisions.",
        action="check_account_status",
        observation=account_status,
        next_step="Apply safety rules to decide whether auto-reply is allowed.",
    )

    never_auto_reply, safety_reason = should_never_auto_reply(email)

    add_trace(
        reasoning_trace,
        thought="Before drafting or sending, apply safety restrictions.",
        action="safety_policy_check",
        observation={
            "never_auto_reply": never_auto_reply,
            "reason": safety_reason,
        },
        next_step="Choose final action type.",
    )

    policy_refs = [item["source_doc"] for item in rag_results]
    proposed_reply = None

    if email.category != "Spam":
        proposed_reply = draft_reply_tool(
            email=email,
            tone="empathetic-professional",
            policy_refs=policy_refs,
        )

    action_type = determine_action_type(email)

    if never_auto_reply:
        final_decision = {
            "action_type": action_type,
            "execute_now": False,
            "requires_approval": True,
            "auto_reply_allowed": False,
            "reason": safety_reason,
        }
    elif email.requires_human:
        final_decision = {
            "action_type": "Escalate",
            "execute_now": False,
            "requires_approval": True,
            "auto_reply_allowed": False,
            "reason": "Human review required by classification.",
        }
    else:
        final_decision = {
            "action_type": "Draft-Reply",
            "execute_now": False,
            "requires_approval": True,
            "auto_reply_allowed": True,
            "reason": "Safe to prepare a draft, but dry-run mode does not execute actions.",
        }

    add_trace(
        reasoning_trace,
        thought="The final action must balance urgency, policy, safety, and customer context.",
        action="decide_final_action",
        observation=final_decision,
        next_step="Return dry-run plan without executing external actions.",
    )

    saved_action_id = None

    if persist:
        action = create_action_record_tool(
            db=db,
            email=email,
            reasoning_log=reasoning_trace,
            action_type=final_decision["action_type"],
            proposed_content=proposed_reply,
            execute=False,
        )
        saved_action_id = action.id

    return {
        "mode": "dry_run",
        "email": {
            "id": email.id,
            "message_id": email.message_id,
            "sender": email.sender,
            "subject": email.subject,
            "category": email.category,
            "urgency": email.urgency,
            "status": email.status,
            "requires_human": email.requires_human,
            "confidence": email.confidence,
        },
        "thread_summary": summarize_thread(thread_history),
        "account_status": account_status,
        "rag_results": rag_results,
        "reasoning_trace": reasoning_trace,
        "proposed_reply": proposed_reply,
        "final_decision": final_decision,
        "saved_action_id": saved_action_id,
    }