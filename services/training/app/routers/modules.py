"""
Training modules router.
POST   /training/modules                -- create a module assignment
GET    /training/modules                -- list all module assignments
GET    /training/modules/{id}           -- retrieve a single assignment
PUT    /training/modules/{id}           -- update title/assignee/due date/description
DELETE /training/modules/{id}           -- remove an assignment
PATCH  /training/modules/{id}/progress  -- update completion percentage
POST   /training/modules/{id}/remind    -- send a reminder if one is due
"""
from dataclasses import replace
from datetime import date
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.models import TrainingModule
from app.services.modules import TrainingModuleService, ModuleRequest
from app.services.progress_tracker import ProgressTrackerService

router = APIRouter(prefix="/training/modules", tags=["training modules"])

_service = TrainingModuleService()
_tracker = ProgressTrackerService()

_MODULE_NOT_FOUND = "Training module not found"


# -- in-memory store ------------------------------------------------------------

class ModuleStore:
    """Owns module-assignment persistence only. Swap for a DB-backed impl without touching the router."""

    def __init__(self) -> None:
        self._store: dict[int, TrainingModule] = {}
        self._next_id: int = 1

    def add(self, module: TrainingModule) -> TrainingModule:
        module.id = self._next_id
        self._store[module.id] = module
        self._next_id += 1
        return module

    def get(self, module_id: int) -> TrainingModule | None:
        return self._store.get(module_id)

    def replace(self, module_id: int, module: TrainingModule) -> None:
        self._store[module_id] = module

    def delete(self, module_id: int) -> bool:
        return self._store.pop(module_id, None) is not None

    def list_all(self) -> list[TrainingModule]:
        return list(self._store.values())


_store = ModuleStore()


# -- schemas ---------------------------------------------------------------------

class ModuleCreate(BaseModel):
    title: str
    assigned_to: str
    due_date: date
    description: str = ""


class ModuleUpdate(BaseModel):
    title: str
    assigned_to: str
    due_date: date
    description: str = ""


class ProgressUpdate(BaseModel):
    completion_pct: float


def _to_dict(module: TrainingModule) -> dict:
    return {
        "id": module.id,
        "title": module.title,
        "assigned_to": module.assigned_to,
        "due_date": module.due_date,
        "description": module.description,
        "completion_pct": module.completion_pct,
        "status": module.status,
        "reminder_count": module.reminder_count,
    }


# -- routes -----------------------------------------------------------------------

@router.post("", status_code=201, responses={422: {"description": "Invalid module request"}})
def create_module(body: ModuleCreate):
    request = ModuleRequest(
        title=body.title,
        assigned_to=body.assigned_to,
        due_date=body.due_date,
        description=body.description,
    )
    try:
        result = _service.create(request)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    module = TrainingModule(
        id=0,
        title=result.title,
        assigned_to=result.assigned_to,
        due_date=result.due_date,
        description=result.description,
        completion_pct=result.completion_pct,
        status=result.status,
    )
    _store.add(module)
    return _to_dict(module)


@router.get("")
def list_modules():
    return [_to_dict(m) for m in _store.list_all()]


@router.get("/{module_id}", responses={404: {"description": _MODULE_NOT_FOUND}})
def get_module(module_id: int):
    module = _store.get(module_id)
    if module is None:
        raise HTTPException(status_code=404, detail=_MODULE_NOT_FOUND)
    return _to_dict(module)


@router.put(
    "/{module_id}",
    responses={
        404: {"description": _MODULE_NOT_FOUND},
        422: {"description": "Invalid module request"},
    },
)
def update_module(module_id: int, body: ModuleUpdate):
    existing = _store.get(module_id)
    if existing is None:
        raise HTTPException(status_code=404, detail=_MODULE_NOT_FOUND)

    request = ModuleRequest(
        title=body.title,
        assigned_to=body.assigned_to,
        due_date=body.due_date,
        description=body.description,
    )
    try:
        result = _service.update(
            request, completion_pct=existing.completion_pct, status=existing.status
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    updated = TrainingModule(
        id=module_id,
        title=result.title,
        assigned_to=result.assigned_to,
        due_date=result.due_date,
        description=result.description,
        completion_pct=result.completion_pct,
        status=result.status,
        reminder_count=existing.reminder_count,
    )
    _store.replace(module_id, updated)
    return _to_dict(updated)


@router.delete("/{module_id}", status_code=204, responses={404: {"description": _MODULE_NOT_FOUND}})
def delete_module(module_id: int):
    if not _store.delete(module_id):
        raise HTTPException(status_code=404, detail=_MODULE_NOT_FOUND)


@router.patch(
    "/{module_id}/progress",
    responses={
        404: {"description": _MODULE_NOT_FOUND},
        422: {"description": "Invalid completion percentage"},
    },
)
def update_progress(module_id: int, body: ProgressUpdate):
    existing = _store.get(module_id)
    if existing is None:
        raise HTTPException(status_code=404, detail=_MODULE_NOT_FOUND)

    try:
        updated = _tracker.update_completion(existing, body.completion_pct)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    _store.replace(module_id, updated)
    return _to_dict(updated)


@router.post(
    "/{module_id}/remind",
    responses={
        404: {"description": _MODULE_NOT_FOUND},
        409: {"description": "No reminder is due for this module"},
    },
)
def remind(module_id: int):
    existing = _store.get(module_id)
    if existing is None:
        raise HTTPException(status_code=404, detail=_MODULE_NOT_FOUND)

    if not _tracker.should_remind(existing, date.today()):
        raise HTTPException(status_code=409, detail="No reminder is due for this module")

    updated = replace(existing, reminder_count=existing.reminder_count + 1)
    _store.replace(module_id, updated)
    return _to_dict(updated)
