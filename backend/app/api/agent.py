from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.agent.triage_agent import run_triage_agent_dry_run
from app.core.responses import success_response
from app.database import get_db


router = APIRouter(prefix="/agent", tags=["Agent"])


@router.post("/dry-run/{email_id}")
def agent_dry_run(
    email_id: int,
    db: Session = Depends(get_db),
):
    result = run_triage_agent_dry_run(
        db=db,
        email_id=email_id,
        persist=True,
    )

    return success_response(
        data=result,
        message="Agent dry run completed successfully.",
    )