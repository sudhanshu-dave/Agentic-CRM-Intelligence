from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Email(Base):
    __tablename__ = "emails"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    thread_db_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("threads.id"),
        index=True,
        nullable=False,
    )

    message_id: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )

    sender: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    subject: Mapped[str] = mapped_column(String(500), default="", nullable=False)
    body: Mapped[str] = mapped_column(Text, default="", nullable=False)

    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        index=True,
        nullable=False,
    )

    sentiment_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    category: Mapped[str] = mapped_column(String(100), default="Other", index=True, nullable=False)
    urgency: Mapped[str] = mapped_column(String(50), default="Low", index=True, nullable=False)

    requires_human: Mapped[bool] = mapped_column(default=False, nullable=False)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)

    raw_entities: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    status: Mapped[str] = mapped_column(
        String(50),
        default="Received",
        index=True,
        nullable=False,
    )

    priority_score: Mapped[int] = mapped_column(Integer, default=0, index=True, nullable=False)

    heuristic_flags: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    thread = relationship("EmailThread", back_populates="emails")

    actions = relationship(
        "Action",
        back_populates="email",
        cascade="all, delete-orphan",
    )