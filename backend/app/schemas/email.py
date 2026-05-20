from datetime import datetime
from typing import Any

from pydantic import BaseModel, EmailStr, Field, field_validator


class EmailIngestRequest(BaseModel):
    message_id: str = Field(..., min_length=1, max_length=255)
    sender: EmailStr
    subject: str | None = Field(default="", max_length=500)
    body: str | None = Field(default="")
    timestamp: datetime
    thread_id: str = Field(..., min_length=1, max_length=255)

    @field_validator("message_id", "thread_id")
    @classmethod
    def not_blank(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("Field cannot be blank.")
        return value.strip()

    @field_validator("subject", "body")
    @classmethod
    def normalize_nullable_text(cls, value: str | None) -> str:
        if value is None:
            return ""
        return value


class EmailIngestResponse(BaseModel):
    job_id: str
    email_id: int
    message_id: str
    thread_id: str
    status: str
    category: str
    urgency: str
    priority_score: int
    requires_human: bool
    heuristic_flags: dict[str, Any]


class EmailStatusResponse(BaseModel):
    job_id: str
    email_id: int
    message_id: str
    processing_status: str
    category: str
    urgency: str
    requires_human: bool