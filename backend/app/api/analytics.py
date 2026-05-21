from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.responses import success_response
from app.database import get_db
from app.models import Email


router = APIRouter(prefix="/analytics", tags=["Analytics"])


def make_timezone_aware(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None

    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)

    return dt


def get_dataset_anchor_time(db: Session) -> datetime:
    """
    Uses the latest email timestamp as the analytics anchor.
    This is better for the demo dataset because emails are from 2023.
    """
    latest_timestamp = db.query(func.max(Email.timestamp)).scalar()
    latest_timestamp = make_timezone_aware(latest_timestamp)

    if latest_timestamp is None:
        return datetime.now(timezone.utc)

    return latest_timestamp


def moving_average(values: list[float], window_size: int = 3) -> list[float]:
    averages = []

    for index in range(len(values)):
        start = max(0, index - window_size + 1)
        window = values[start : index + 1]
        averages.append(round(sum(window) / len(window), 4))

    return averages


@router.get("/sentiment-trend")
def get_sentiment_trend(
    sender: str | None = Query(default=None),
    days: int = Query(default=30, ge=1, le=365),
    db: Session = Depends(get_db),
):
    anchor_time = get_dataset_anchor_time(db)
    start_time = anchor_time - timedelta(days=days)

    query = db.query(Email).filter(
        Email.timestamp >= start_time,
        Email.timestamp <= anchor_time,
        Email.sentiment_score.isnot(None),
    )

    if sender:
        query = query.filter(Email.sender == sender)

    emails = query.order_by(Email.timestamp.asc()).all()

    daily_scores: dict[str, list[float]] = defaultdict(list)

    for email in emails:
        day = email.timestamp.date().isoformat()
        daily_scores[day].append(float(email.sentiment_score))

    trend_points = []

    for day in sorted(daily_scores.keys()):
        scores = daily_scores[day]
        avg_score = round(sum(scores) / len(scores), 4)

        trend_points.append(
            {
                "date": day,
                "average_sentiment_score": avg_score,
                "email_count": len(scores),
            }
        )

    moving_values = moving_average(
        [point["average_sentiment_score"] for point in trend_points],
        window_size=3,
    )

    for index, value in enumerate(moving_values):
        trend_points[index]["moving_average_3_day"] = value

    consecutive_negative_count = 0
    deterioration_alert = False

    for email in emails:
        if email.sentiment_score is not None and email.sentiment_score < 0:
            consecutive_negative_count += 1
        else:
            consecutive_negative_count = 0

        if consecutive_negative_count >= 3:
            deterioration_alert = True
            break

    return success_response(
        data={
            "sender": sender,
            "window_days": days,
            "anchor_time": anchor_time.isoformat(),
            "start_time": start_time.isoformat(),
            "total_classified_emails": len(emails),
            "deterioration_alert": deterioration_alert,
            "trend": trend_points,
        },
        message="Sentiment trend retrieved successfully.",
    )


@router.get("/category-breakdown")
def get_category_breakdown(
    days: int = Query(default=30, ge=1, le=365),
    sender: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    anchor_time = get_dataset_anchor_time(db)
    start_time = anchor_time - timedelta(days=days)

    query = db.query(Email).filter(
        Email.timestamp >= start_time,
        Email.timestamp <= anchor_time,
    )

    if sender:
        query = query.filter(Email.sender == sender)

    total = query.count()

    category_rows = (
        query.with_entities(Email.category, func.count(Email.id))
        .group_by(Email.category)
        .order_by(func.count(Email.id).desc())
        .all()
    )

    urgency_rows = (
        query.with_entities(Email.urgency, func.count(Email.id))
        .group_by(Email.urgency)
        .order_by(func.count(Email.id).desc())
        .all()
    )

    status_rows = (
        query.with_entities(Email.status, func.count(Email.id))
        .group_by(Email.status)
        .order_by(func.count(Email.id).desc())
        .all()
    )

    category_breakdown: list[dict[str, Any]] = []

    for category, count in category_rows:
        percentage = round((count / total) * 100, 2) if total else 0

        category_breakdown.append(
            {
                "category": category,
                "count": count,
                "percentage": percentage,
            }
        )

    urgency_breakdown = [
        {
            "urgency": urgency,
            "count": count,
            "percentage": round((count / total) * 100, 2) if total else 0,
        }
        for urgency, count in urgency_rows
    ]

    status_breakdown = [
        {
            "status": status,
            "count": count,
            "percentage": round((count / total) * 100, 2) if total else 0,
        }
        for status, count in status_rows
    ]

    return success_response(
        data={
            "sender": sender,
            "window_days": days,
            "anchor_time": anchor_time.isoformat(),
            "start_time": start_time.isoformat(),
            "total_emails": total,
            "category_breakdown": category_breakdown,
            "urgency_breakdown": urgency_breakdown,
            "status_breakdown": status_breakdown,
        },
        message="Category breakdown retrieved successfully.",
    )