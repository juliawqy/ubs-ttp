"""
Feedback router.
POST /feedback              -- submit one rater's free-text 360 feedback about
                               an employee; returns the entry as recorded
GET  /feedback/{employee_id} -- anonymised, aggregated feedback for an employee
                               (no rater identity in the response at all)

Unlike reviews.py, this router owns no separate *Store: FeedbackService
itself owns persistence (see app/services/feedback.py docstring for why),
so the router only ever talks to the service.
"""
from typing import Annotated
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from app.services.feedback import FeedbackService

router = APIRouter(prefix="/feedback", tags=["feedback"])

_feedback_service = FeedbackService()

_IdStr = Annotated[str, Field(pattern=r"^[a-zA-Z0-9_-]+$", min_length=1)]


# -- schemas ---------------------------------------------------------------------

class FeedbackCreate(BaseModel):
    employee_id: _IdStr
    rater_id: _IdStr
    comments: str


# -- helpers ----------------------------------------------------------------------

def _entry_to_dict(entry) -> dict:
    return {
        "employee_id": entry.employee_id,
        "rater_id": entry.rater_id,
        "comments": entry.comments,
    }


def _aggregated_to_dict(aggregated) -> dict:
    return {
        "employee_id": aggregated.employee_id,
        "comments": aggregated.comments,
        "count": aggregated.count,
    }


# -- routes -----------------------------------------------------------------------

@router.post("", status_code=201, responses={422: {"description": "Invalid feedback submission"}})
def submit_feedback(body: FeedbackCreate):
    try:
        entry = _feedback_service.submit(body.employee_id, body.rater_id, body.comments)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    return _entry_to_dict(entry)


@router.get("/{employee_id}")
def get_aggregated_feedback(employee_id: str):
    aggregated = _feedback_service.get_aggregated(employee_id)
    return _aggregated_to_dict(aggregated)
