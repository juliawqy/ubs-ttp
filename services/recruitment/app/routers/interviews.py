"""
Interviews router.
POST /interviews/assign-panel — assign a diverse interview panel from a given pool
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from app.services.panel_assignment import Interviewer, PanelAssignmentService, MIN_PANEL_SIZE

router = APIRouter(prefix="/interviews", tags=["interviews"])

_panel_service = PanelAssignmentService()


# ── schemas ───────────────────────────────────────────────────────────────────

class InterviewerIn(BaseModel):
    id: str = Field(..., example="iv-001")
    name: str = Field(..., example="Alice Smith")
    gender: str = Field(..., example="Female")
    department: str = Field(..., example="Engineering")
    seniority: str = Field(default="", example="Senior")


class AssignPanelRequest(BaseModel):
    interviewer_pool: list[InterviewerIn] = Field(
        ...,
        example=[
            {"id": "iv-001", "name": "Alice Smith",  "gender": "Female", "department": "Engineering", "seniority": "Senior"},
            {"id": "iv-002", "name": "Bob Jones",    "gender": "Male",   "department": "Engineering", "seniority": "Mid"},
            {"id": "iv-003", "name": "Carol Lee",    "gender": "Female", "department": "HR",          "seniority": "Senior"},
            {"id": "iv-004", "name": "David Tan",    "gender": "Male",   "department": "Product",     "seniority": "Lead"},
        ],
    )
    panel_size: int = Field(default=MIN_PANEL_SIZE, ge=MIN_PANEL_SIZE, example=3)
    mandatory_ids: list[str] = Field(default=[], example=[])


# ── routes ────────────────────────────────────────────────────────────────────

@router.post("/assign-panel")
def assign_panel(body: AssignPanelRequest):
    pool = [
        Interviewer(id=iv.id, name=iv.name, gender=iv.gender, department=iv.department, seniority=iv.seniority)
        for iv in body.interviewer_pool
    ]

    try:
        result = _panel_service.assign(
            pool,
            panel_size=body.panel_size,
            mandatory_ids=body.mandatory_ids,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    return {
        "approved": result.approved,
        "interviewers": [
            {"id": iv.id, "name": iv.name, "gender": iv.gender, "department": iv.department, "seniority": iv.seniority}
            for iv in result.interviewers
        ],
        "rejection_reason": result.rejection_reason,
    }
