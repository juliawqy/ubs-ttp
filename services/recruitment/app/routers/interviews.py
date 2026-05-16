"""
Interviews router.
POST /interviews/assign-panel — assign a diverse interview panel from a given pool
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.panel_assignment import Interviewer, PanelAssignmentService, MIN_PANEL_SIZE

router = APIRouter(prefix="/interviews", tags=["interviews"])

_panel_service = PanelAssignmentService()


# ── schemas ───────────────────────────────────────────────────────────────────

class InterviewerIn(BaseModel):
    id: str
    name: str
    gender: str
    department: str


class AssignPanelRequest(BaseModel):
    interviewer_pool: list[InterviewerIn]
    panel_size: int = MIN_PANEL_SIZE
    mandatory_ids: list[str] = []


# ── routes ────────────────────────────────────────────────────────────────────

@router.post("/assign-panel")
def assign_panel(body: AssignPanelRequest):
    pool = [
        Interviewer(id=iv.id, name=iv.name, gender=iv.gender, department=iv.department)
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
            {"id": iv.id, "name": iv.name, "gender": iv.gender, "department": iv.department}
            for iv in result.interviewers
        ],
        "rejection_reason": result.rejection_reason,
    }
