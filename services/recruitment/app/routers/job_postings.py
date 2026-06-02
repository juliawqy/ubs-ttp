"""
Job postings router.
Accepts a manager's request to open a new role and passes it to
JobPostingsService. Business logic (validation, bias check) lives
in the service — the router owns only HTTP and in-memory storage.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from app.services.job_postings import (
    JobPostingsService,
    JobPostingRequest,
    HiringManager,
)

router = APIRouter(prefix="/job-postings", tags=["job postings"])

_service = JobPostingsService()

# ── in-memory store ───────────────────────────────────────────────────────────
_store: dict[int, dict] = {}
_next_id = 1


# ── schemas ───────────────────────────────────────────────────────────────────

class HiringManagerIn(BaseModel):
    id: str
    name: str
    department: str
    email: EmailStr


class JobPostingCreate(BaseModel):
    title: str
    description: str
    requirements: list[str]
    department: str
    manager: HiringManagerIn


# ── routes ────────────────────────────────────────────────────────────────────

@router.get("")
def list_job_postings():
    return list(_store.values())


@router.post("", status_code=201)
def create_job_posting(body: JobPostingCreate):
    global _next_id

    request = JobPostingRequest(
        title=body.title,
        description=body.description,
        requirements=body.requirements,
        department=body.department,
        manager=HiringManager(
            id=body.manager.id,
            name=body.manager.name,
            department=body.manager.department,
            email=body.manager.email,
        ),
    )

    try:
        result = _service.create_request(request)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    posting = {
        "id": _next_id,
        "title": result.title,
        "description": result.description,
        "requirements": result.requirements,
        "department": result.department,
        "manager": {
            "id": result.manager.id,
            "name": result.manager.name,
            "department": result.manager.department,
            "email": result.manager.email,
        },
        "status": result.status,
        "bias_check": {
            "flagged": result.bias_check.flagged,
            "flagged_phrases": [
                {"phrase": fp.phrase, "reason": fp.reason, "suggestion": fp.suggestion}
                for fp in result.bias_check.flagged_phrases
            ],
        },
    }
    _store[_next_id] = posting
    _next_id += 1
    return posting


@router.get("/{posting_id}")
def get_job_posting(posting_id: str):
    try:
        pid = int(posting_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Job posting not found")

    if pid not in _store:
        raise HTTPException(status_code=404, detail="Job posting not found")

    return _store[pid]
