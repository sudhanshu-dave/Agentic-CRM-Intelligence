from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Action(Base):
    __tablename__ = "actions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    email_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("emails.id"),
        index=True,
        nullable=False,
    )

    agent_reasoning_log: Mapped[list | dict | None] = mapped_column(JSON, nullable=True)

    action_type: Mapped[str] = mapped_column(
        String(100),
        index=True,
        nullable=False,
    )

    proposed_content: Mapped[str | None] = mapped_column(Text, nullable=True)

    is_approved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    approved_by: Mapped[str | None] = mapped_column(String(255), nullable=True)

    executed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    email = relationship("Email", back_populates="actions")