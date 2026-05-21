from typing import Any

from sqlalchemy.orm import Session

from app.models import Action, Contact, Email
from app.rag.retriever import search_knowledge_base


def get_thread_history_tool(email: Email) -> dict[str, Any]:
    if not email.thread:
        return {
            "thread_id": None,
            "emails": [],
        }

    return {
        "thread_id": email.thread.thread_id,
        "status": email.thread.status,
        "emails": [
            {
                "message_id": item.message_id,
                "sender": item.sender,
                "subject": item.subject,
                "body": item.body,
                "timestamp": item.timestamp.isoformat() if item.timestamp else None,
                "category": item.category,
                "urgency": item.urgency,
                "status": item.status,
            }
            for item in email.thread.emails
        ],
    }


def get_contact_profile_tool(db: Session, email_address: str) -> dict[str, Any]:
    contact = db.query(Contact).filter(Contact.email == email_address).first()

    if not contact:
        return {
            "email": email_address,
            "found": False,
        }

    return {
        "found": True,
        "email": contact.email,
        "name": contact.name,
        "company": contact.company,
        "status": contact.status,
        "account_value": contact.account_value,
        "churn_risk_score": contact.churn_risk_score,
        "last_contact_at": contact.last_contact_at.isoformat() if contact.last_contact_at else None,
    }


def check_account_status_tool(email_address: str) -> dict[str, Any]:
    """
    Demo CRM/account lookup.
    In production this would call billing/CRM systems.
    """
    known_accounts = {
        "bob.jones@enterprise.net": {
            "tier": "Enterprise",
            "account_value": 180000,
            "renewal_status": "On hold due to incident escalation",
            "open_invoices": 0,
            "sla_covered": True,
            "account_owner": "enterprise-csm@company.com",
        },
        "karen.w@retail-co.com": {
            "tier": "Professional",
            "account_value": 12000,
            "renewal_status": "At risk",
            "open_invoices": 0,
            "sla_covered": False,
            "account_owner": "customer-success@company.com",
        },
        "marcus.del@fintech-startup.co": {
            "tier": "Professional",
            "account_value": 9000,
            "renewal_status": "Active",
            "open_invoices": 0,
            "sla_covered": False,
            "account_owner": "privacy-ops@company.com",
        },
        "hacker@anon-collective.net": {
            "tier": "Unknown",
            "account_value": 0,
            "renewal_status": "Not a customer account",
            "open_invoices": 0,
            "sla_covered": False,
            "account_owner": "security-incident-response@company.com",
        },
        "user.confused@hotmail.com": {
            "tier": "Standard",
            "account_value": 1200,
            "renewal_status": "Active",
            "open_invoices": 0,
            "sla_covered": False,
            "account_owner": "support-lead@company.com",
        },
    }

    default_profile = {
        "tier": "Unknown",
        "account_value": 0,
        "renewal_status": "Unknown",
        "open_invoices": 0,
        "sla_covered": False,
        "account_owner": "support@company.com",
    }

    return known_accounts.get(email_address, default_profile)


def draft_reply_tool(
    email: Email,
    tone: str,
    policy_refs: list[str],
) -> str:
    subject = email.subject.lower()
    body = email.body.lower()

    if "gdpr" in body or "article 20" in body or "data portability" in body:
        return (
            "Hello,\n\n"
            "We acknowledge receipt of your data portability request. "
            "Your request has been routed to our privacy operations team for review. "
            "They will process it according to the applicable statutory response window. "
            "For your security, we may need to verify your identity before releasing account data.\n\n"
            "Regards,\n"
            "Support Team\n\n"
            f"Policy references: {', '.join(policy_refs)}"
        )

    if "legal" in body or "sla" in body or "rca" in body or "renewal" in body:
        return (
            "Hello,\n\n"
            "Thank you for the update. We understand the seriousness of your concerns regarding "
            "the incident review, SLA credit process, and renewal impact. We are escalating this "
            "to our Legal, Support Leadership, and Customer Success teams for immediate review. "
            "We will follow up with a coordinated response after validating the incident record, "
            "contract terms, and RCA obligations.\n\n"
            "Regards,\n"
            "Enterprise Support Team\n\n"
            f"Policy references: {', '.join(policy_refs)}"
        )

    if "refund" in body or "review" in body or "trustpilot" in body or "g2" in body:
        return (
            "Hello,\n\n"
            "Thank you for sharing this. We are sorry for the delay and understand your frustration. "
            "Your case has been escalated to a support lead for urgent review, including your refund "
            "request and account history. We will prioritize a human follow-up rather than sending a "
            "generic response.\n\n"
            "Regards,\n"
            "Customer Support Team\n\n"
            f"Policy references: {', '.join(policy_refs)}"
        )

    if "chatbot" in body and "refund" in body:
        return (
            "Hello,\n\n"
            "Thank you for flagging the discrepancy between the chatbot response and the billing policy. "
            "We are escalating this for review so the team can compare the chatbot guidance with the current "
            "refund policy and follow up carefully.\n\n"
            "Regards,\n"
            "Support Team\n\n"
            f"Policy references: {', '.join(policy_refs)}"
        )

    return (
        "Hello,\n\n"
        "Thank you for contacting us. We have reviewed your message and routed it to the appropriate team.\n\n"
        "Regards,\n"
        "Support Team\n\n"
        f"Policy references: {', '.join(policy_refs)}"
    )


def create_action_record_tool(
    db: Session,
    email: Email,
    reasoning_log: list[dict[str, Any]],
    action_type: str,
    proposed_content: str | None,
    execute: bool = False,
) -> Action:
    action = Action(
        email_id=email.id,
        agent_reasoning_log=reasoning_log,
        action_type=action_type,
        proposed_content=proposed_content,
        is_approved=False,
        approved_by=None,
        executed_at=None,
    )

    db.add(action)

    if execute:
        email.status = "Escalated"

        if email.thread:
            email.thread.status = "Escalated"

    db.commit()
    db.refresh(action)

    return action


def search_knowledge_base_tool(
    db: Session,
    query: str,
    top_k: int = 3,
) -> list[dict[str, Any]]:
    return search_knowledge_base(db=db, query=query, top_k=top_k)