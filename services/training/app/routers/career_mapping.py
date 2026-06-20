"""
Career path mapping router.
Tracks each employee's current role, next milestone, and the skills
recommended to bridge the two. Recommendations come from RecommendationEngine
via CareerPathService -- the router owns HTTP and storage only.
"""
from datetime import date
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.career_mapping import CareerPathService, CareerPathRequest

router = APIRouter(prefix="/training/career-mapping", tags=["career mapping"])

_service = CareerPathService()

# -- in-memory store ------------------------------------------------------------
_store: dict[int, dict] = {}
_next_id = 1


# -- schemas ---------------------------------------------------------------------

class CareerPathCreate(BaseModel):
    employee_name: str
    current_role: str
    next_milestone: str
    target_date: date


class CareerPathUpdate(BaseModel):
    employee_name: str
    current_role: str
    next_milestone: str
    target_date: date


def _build_entry(entry_id: int, result) -> dict:
    return {
        "id": entry_id,
        "employee_name": result.employee_name,
        "current_role": result.current_role,
        "next_milestone": result.next_milestone,
        "target_date": result.target_date,
        "recommended_skills": result.recommended_skills,
    }


# -- routes -----------------------------------------------------------------------

@router.post("", status_code=201)
def create_entry(body: CareerPathCreate):
    global _next_id

    request = CareerPathRequest(**body.model_dump())
    try:
        result = _service.create_entry(request)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    entry = _build_entry(_next_id, result)
    _store[_next_id] = entry
    _next_id += 1
    return entry


@router.get("")
def list_entries():
    return list(_store.values())


@router.get("/{entry_id}")
def get_entry(entry_id: int):
    if entry_id not in _store:
        raise HTTPException(status_code=404, detail="Career path entry not found")
    return _store[entry_id]


@router.put("/{entry_id}")
def update_entry(entry_id: int, body: CareerPathUpdate):
    if entry_id not in _store:
        raise HTTPException(status_code=404, detail="Career path entry not found")

    request = CareerPathRequest(**body.model_dump())
    try:
        result = _service.create_entry(request)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    entry = _build_entry(entry_id, result)
    _store[entry_id] = entry
    return entry


@router.delete("/{entry_id}", status_code=204)
def delete_entry(entry_id: int):
    if entry_id not in _store:
        raise HTTPException(status_code=404, detail="Career path entry not found")
    del _store[entry_id]
