from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class EmailThread(Base):
    __tablename__ = "threads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    thread_id: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    subject: Mapped[str | None] = mapped_column(String(500), nullable=True)

    sender_email: Mapped[str] = mapped_column(
        String(255),
        ForeignKey("contacts.email"),
        index=True,
        nullable=False,
    )

    first_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    last_updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(String(50), default="Open", nullable=False)
    assigned_to: Mapped[str | None] = mapped_column(String(255), nullable=True)

    contact = relationship("Contact", back_populates="threads")

    emails = relationship(
        "Email",
        back_populates="thread",
        cascade="all, delete-orphan",
        order_by="Email.timestamp",
    )