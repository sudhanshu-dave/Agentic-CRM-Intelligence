import json
from typing import Any

from app.models import Email


SYSTEM_PROMPT = """
You are an AI CRM email classification engine.

Your job:
1. Classify the customer email.
2. Use full thread history.
3. Use retrieved internal policy context.
4. Return only structured JSON matching the schema.
5. Never invent policy.
6. Never say an email is safe if it involves legal, GDPR/privacy, ransomware, security threats, or critical incidents.

Safety rules:
- Spam must not receive a reply.
- Security threats must not receive a reply.
- Legal threats require human review.
- GDPR/privacy requests require privacy/legal routing.
- Critical incidents require human review.
- Public review threats require human escalation.
- Refund promises must not be made without approval.
"""


def build_llm_classification_messages(
    email: Email,
    thread_context: str,
    rag_results: list[dict[str, Any]],
) -> list[dict[str, str]]:
    email_payload = {
        "id": email.id,
        "message_id": email.message_id,
        "sender": email.sender,
        "subject": email.subject,
        "body": email.body,
        "timestamp": email.timestamp.isoformat() if email.timestamp else None,
        "heuristic_category": email.category,
        "heuristic_urgency": email.urgency,
        "heuristic_flags": email.heuristic_flags,
        "priority_score": email.priority_score,
    }

    rag_payload = [
        {
            "source_doc": item.get("source_doc"),
            "similarity_score": item.get("similarity_score"),
            "chunk_text": item.get("chunk_text"),
        }
        for item in rag_results
    ]

    user_prompt = {
        "email": email_payload,
        "thread_context": thread_context,
        "retrieved_policy_context": rag_payload,
        "instructions": {
            "classification_categories": [
                "Inquiry",
                "Billing",
                "Bug Report",
                "Feature Request",
                "Complaint",
                "Legal",
                "Compliance",
                "Spam",
                "Internal",
                "Other",
            ],
            "urgency_levels": ["Low", "Medium", "High", "Critical"],
            "sentiment_score_range": "-1.0 negative to +1.0 positive",
            "important": "Use the retrieved policies as grounding. Do not auto-resolve legal, privacy, security, or critical cases.",
        },
    }

    return [
        {
            "role": "system",
            "content": SYSTEM_PROMPT.strip(),
        },
        {
            "role": "user",
            "content": json.dumps(user_prompt, indent=2),
        },
    ]