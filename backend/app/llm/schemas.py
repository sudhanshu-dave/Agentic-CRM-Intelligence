LLM_CLASSIFICATION_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "category": {
            "type": "string",
            "enum": [
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
        },
        "sentiment": {
            "type": "string",
            "enum": ["Positive", "Neutral", "Negative"],
        },
        "sentiment_score": {
            "type": "number",
            "minimum": -1,
            "maximum": 1,
        },
        "urgency": {
            "type": "string",
            "enum": ["Low", "Medium", "High", "Critical"],
        },
        "requires_human": {
            "type": "boolean",
        },
        "escalation_reason": {
            "type": ["string", "null"],
        },
        "suggested_reply": {
            "type": ["string", "null"],
        },
        "confidence": {
            "type": "number",
            "minimum": 0,
            "maximum": 1,
        },
        "detected_entities": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "order_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "ticket_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "monetary_amounts": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "deadlines": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "products_mentioned": {
                    "type": "array",
                    "items": {"type": "string"},
                },
            },
            "required": [
                "order_ids",
                "ticket_ids",
                "monetary_amounts",
                "deadlines",
                "products_mentioned",
            ],
        },
        "policy_refs": {
            "type": "array",
            "items": {"type": "string"},
        },
        "model_reasoning_summary": {
            "type": "string",
        },
    },
    "required": [
        "category",
        "sentiment",
        "sentiment_score",
        "urgency",
        "requires_human",
        "escalation_reason",
        "suggested_reply",
        "confidence",
        "detected_entities",
        "policy_refs",
        "model_reasoning_summary",
    ],
}