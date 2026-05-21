from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload

from app.core.errors import AppError
from app.core.responses import success_response
from app.database import get_db
from app.models import Action


router = APIRouter(prefix="/actions", tags=["Actions"])


class ActionApprovalRequest(BaseModel):
    approved_by: str = "human_reviewer"


class ActionRejectionRequest(BaseModel):
    rejected_by: str = "human_reviewer"
    reason: str | None = None


def is_rejected(action: Action) -> bool:
    return bool(action.approved_by and action.approved_by.startswith("Rejected by"))


def serialize_action(action: Action):
    return {
        "id": action.id,
        "email_id": action.email_id,
        "action_type": action.action_type,
        "agent_reasoning_log": action.agent_reasoning_log,
        "proposed_content": action.proposed_content,
        "is_approved": action.is_approved,
        "approved_by": action.approved_by,
        "executed_at": action.executed_at.isoformat() if action.executed_at else None,
        "created_at": action.created_at.isoformat() if action.created_at else None,
        "review_status": (
            "Approved"
            if action.is_approved
            else "Rejected"
            if is_rejected(action)
            else "Pending"
        ),
        "email": {
            "id": action.email.id if action.email else None,
            "message_id": action.email.message_id if action.email else None,
            "sender": action.email.sender if action.email else None,
            "subject": action.email.subject if action.email else None,
            "category": action.email.category if action.email else None,
            "urgency": action.email.urgency if action.email else None,
            "status": action.email.status if action.email else None,
        },
    }


@router.get("/pending")
def get_pending_actions(
    limit: int = 25,
    db: Session = Depends(get_db),
):
    actions = (
        db.query(Action)
        .options(joinedload(Action.email))
        .filter(Action.is_approved.is_(False))
        .filter(Action.approved_by.is_(None))
        .filter(Action.executed_at.is_(None))
        .order_by(Action.created_at.desc())
        .limit(limit)
        .all()
    )

    return success_response(
        data={
            "items": [serialize_action(action) for action in actions],
            "count": len(actions),
        },
        message="Pending actions retrieved successfully.",
    )


@router.post("/{action_id}/approve")
def approve_action(
    action_id: int,
    payload: ActionApprovalRequest,
    db: Session = Depends(get_db),
):
    action = (
        db.query(Action)
        .options(joinedload(Action.email))
        .filter(Action.id == action_id)
        .first()
    )

    if not action:
        raise AppError(
            status_code=404,
            error_code="ACTION_NOT_FOUND",
            message="No action found for this id.",
            details={"action_id": action_id},
        )

    if action.is_approved:
        raise AppError(
            status_code=409,
            error_code="ACTION_ALREADY_APPROVED",
            message="This action has already been approved.",
            details={"action_id": action_id},
        )

    if is_rejected(action):
        raise AppError(
            status_code=409,
            error_code="ACTION_ALREADY_REJECTED",
            message="This action has already been rejected and cannot be approved.",
            details={"action_id": action_id},
        )

    action.is_approved = True
    action.approved_by = payload.approved_by
    action.executed_at = datetime.now(timezone.utc)

    if action.email:
        if action.action_type in {"Legal-Flag", "Security-Escalation", "Escalate"}:
            action.email.status = "Escalated"
        elif action.action_type == "Ignored":
            action.email.status = "Ignored"
        else:
            action.email.status = "Processing"

    db.commit()
    db.refresh(action)

    return success_response(
        data=serialize_action(action),
        message="Action approved successfully.",
    )


@router.post("/{action_id}/reject")
def reject_action(
    action_id: int,
    payload: ActionRejectionRequest,
    db: Session = Depends(get_db),
):
    action = (
        db.query(Action)
        .options(joinedload(Action.email))
        .filter(Action.id == action_id)
        .first()
    )

    if not action:
        raise AppError(
            status_code=404,
            error_code="ACTION_NOT_FOUND",
            message="No action found for this id.",
            details={"action_id": action_id},
        )

    if action.is_approved:
        raise AppError(
            status_code=409,
            error_code="ACTION_ALREADY_APPROVED",
            message="This action has already been approved and cannot be rejected.",
            details={"action_id": action_id},
        )

    if is_rejected(action):
        raise AppError(
            status_code=409,
            error_code="ACTION_ALREADY_REJECTED",
            message="This action has already been rejected.",
            details={"action_id": action_id},
        )

    action.is_approved = False
    action.approved_by = f"Rejected by {payload.rejected_by}"
    action.executed_at = None

    if action.email:
        action.email.status = "Escalated" if action.email.requires_human else "Processing"

    db.commit()
    db.refresh(action)

    return success_response(
        data={
            **serialize_action(action),
            "rejection_reason": payload.reason,
        },
        message="Action rejected successfully.",
    )