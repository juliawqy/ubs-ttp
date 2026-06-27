"""
Implicit Association Test (IAT) router.
GET  /training/iat/categories                     -- list available test categories
POST /training/iat/sessions                      -- start a session
POST /training/iat/sessions/{id}/responses        -- submit one response
POST /training/iat/sessions/{id}/complete         -- finish and score a session
GET  /training/iat/sessions/{id}/result           -- fetch a result (owner only)

Results are private: get_result enforces that only the employee who took
the test can read it, never their manager or HR.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.iat import IATService, IATSession, IATResult
from app.services.iat_categories import IATCategoryCatalog, IATCategory

router = APIRouter(prefix="/training/iat", tags=["iat"])

_service = IATService()
_categories_catalog = IATCategoryCatalog()


class IATSessionStore:
    """Owns session/result persistence only. Swap for a DB-backed impl without touching the router."""

    def __init__(self) -> None:
        self._sessions: dict[int, IATSession] = {}
        self._results: dict[int, IATResult] = {}
        self._next_id: int = 1

    def reserve_id(self) -> int:
        session_id = self._next_id
        self._next_id += 1
        return session_id

    def add(self, session: IATSession) -> None:
        self._sessions[session.id] = session

    def get_session(self, session_id: int) -> IATSession | None:
        return self._sessions.get(session_id)

    def save_result(self, session_id: int, result: IATResult) -> None:
        self._results[session_id] = result

    def get_result(self, session_id: int) -> IATResult | None:
        return self._results.get(session_id)


_store = IATSessionStore()


class SessionCreate(BaseModel):
    employee_id: str


class ResponseSubmit(BaseModel):
    category: str
    selected_pole: str
    response_time_ms: float


def _session_to_dict(session: IATSession) -> dict:
    return {
        "id": session.id,
        "employee_id": session.employee_id,
        "status": session.status,
        "response_count": len(session.responses),
    }


def _result_to_dict(result: IATResult) -> dict:
    return {
        "session_id": result.session_id,
        "employee_id": result.employee_id,
        "category_scores": result.category_scores,
    }


def _category_to_dict(category: IATCategory) -> dict:
    return {
        "id": category.id,
        "label": category.label,
        "pole_a": category.pole_a,
        "pole_b": category.pole_b,
        "stimuli": category.stimuli,
    }


@router.get("/categories")
def list_categories():
    return [_category_to_dict(c) for c in _categories_catalog.get_categories()]


@router.post("/sessions", status_code=201)
def start_session(body: SessionCreate):
    session_id = _store.reserve_id()
    try:
        session = _service.start_session(session_id, body.employee_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    _store.add(session)
    return _session_to_dict(session)


@router.post("/sessions/{session_id}/responses")
def submit_response(session_id: int, body: ResponseSubmit):
    session = _store.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="IAT session not found")

    try:
        _service.submit_response(
            session, body.category, body.selected_pole, body.response_time_ms
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    return _session_to_dict(session)


@router.post("/sessions/{session_id}/complete")
def complete_session(session_id: int):
    session = _store.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="IAT session not found")

    try:
        result = _service.complete_session(session)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    _store.save_result(session_id, result)
    return _result_to_dict(result)


@router.get("/sessions/{session_id}/result")
def get_result(session_id: int, employee_id: str):
    result = _store.get_result(session_id)
    if result is None:
        if _store.get_session(session_id) is None:
            raise HTTPException(status_code=404, detail="IAT session not found")
        raise HTTPException(status_code=409, detail="This session has not been completed yet")

    try:
        result = _service.get_result(result, employee_id)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc))

    return _result_to_dict(result)
