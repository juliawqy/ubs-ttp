"""
Candidates router.
POST /candidates/upload      -- ingest a CV (PDF), redact PII, return blind profile
GET  /candidates             -- list all stored blind profiles
GET  /candidates/{id}        -- retrieve a single blind profile by ID
POST /candidates/assess      -- score a candidate against weighted criteria
POST /candidates/{id}/decide -- record a hire/reject decision with bias check
"""
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel, Field
from shared.document_parser.pdf_parser import PDFParser
from shared.document_parser.pii_redactor import PIIRedactor
from shared.bias_analyzer.bias_analyzer import BiasAnalyzer
from app.services.skills_assessment import SkillsAssessmentService
from app.services.hire_decision import HireDecisionService
from app.models import AssessmentCriteria

router = APIRouter(prefix="/candidates", tags=["candidates"])

_pdf_parser = PDFParser()
_redactor = PIIRedactor()
_assessment_service = SkillsAssessmentService()
_decision_service = HireDecisionService(bias_analyzer=BiasAnalyzer())

ALLOWED_CONTENT_TYPES = {"application/pdf"}


# -- in-memory store ----------------------------------------------------------

class CandidateStore:
    """Owns candidate data persistence only. Swap for a DB-backed impl without touching the router."""

    def __init__(self) -> None:
        self._store: dict[int, dict] = {}
        self._next_id: int = 1

    def add(self, redacted_text: str, pii_map: dict) -> int:
        """Store a new blind profile. Returns the assigned candidate_id."""
        candidate_id = self._next_id
        self._store[candidate_id] = {
            "id": candidate_id,
            "redacted_text": redacted_text,
            "status": "pending",
            "decision": None,
            "_pii_map": pii_map,
        }
        self._next_id += 1
        return candidate_id

    def get(self, candidate_id: int) -> dict | None:
        """Return a single candidate profile (without PII map), or None if not found."""
        entry = self._store.get(candidate_id)
        if entry is None:
            return None
        return {
            "candidate_id": entry["id"],
            "redacted_text": entry["redacted_text"],
            "status": entry["status"],
            "decision": entry["decision"],
        }

    def update_status(self, candidate_id: int, status: str, decision_summary: dict) -> None:
        """Update status and store the decision summary for a candidate."""
        if candidate_id not in self._store:
            raise KeyError(candidate_id)
        self._store[candidate_id]["status"] = status
        self._store[candidate_id]["decision"] = decision_summary

    def list_public(self) -> list[dict]:
        """Return all profiles, stripping the PII map."""
        return [
            {
                "candidate_id": c["id"],
                "redacted_text": c["redacted_text"],
                "status": c["status"],
            }
            for c in self._store.values()
        ]


_store = CandidateStore()


# -- schemas ------------------------------------------------------------------

class CriterionIn(BaseModel):
    name: str = Field(..., example="python")
    weight: float = Field(..., ge=0, le=1, example=0.6)
    required: bool = Field(..., example=True)


class AssessRequest(BaseModel):
    criteria: list[CriterionIn] = Field(
        ...,
        example=[
            {"name": "python", "weight": 0.6, "required": True},
            {"name": "sql",    "weight": 0.4, "required": True},
        ],
    )
    scores: dict[str, float] = Field(
        ...,
        example={"python": 8.0, "sql": 7.0},
    )


class AssessResponse(BaseModel):
    total_score: float
    breakdown: dict


class DecideRequest(BaseModel):
    decision: str = Field(..., example="hired")
    justification: str = Field(
        ...,
        example="Strong Python skills and clear communication throughout the process.",
    )


class DecideResponse(BaseModel):
    candidate_id: int
    decision: str
    bias_check: dict


# -- routes -------------------------------------------------------------------

@router.post("/upload")
async def upload_candidate(file: UploadFile = File(...)):
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    raw = await file.read()

    try:
        text = _pdf_parser.extract_text_from_bytes(raw)
    except Exception:
        text = ""

    redacted_text, pii_map = _redactor.redact(text)
    candidate_id = _store.add(redacted_text, pii_map)

    return {"candidate_id": candidate_id, "redacted_text": redacted_text}


@router.get("")
def list_candidates():
    return _store.list_public()


@router.get("/{candidate_id}")
def get_candidate(candidate_id: int):
    candidate = _store.get(candidate_id)
    if candidate is None:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return candidate


@router.post("/assess", response_model=AssessResponse)
def assess_candidate(body: AssessRequest):
    criteria = [
        AssessmentCriteria(name=c.name, weight=c.weight, required=c.required)
        for c in body.criteria
    ]
    try:
        result = _assessment_service.score(body.scores, criteria)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    return AssessResponse(total_score=result.total_score, breakdown=result.breakdown)


@router.post("/{candidate_id}/decide", response_model=DecideResponse)
def decide_candidate(candidate_id: int, body: DecideRequest):
    if _store.get(candidate_id) is None:
        raise HTTPException(status_code=404, detail="Candidate not found")

    try:
        result = _decision_service.record(candidate_id, body.decision, body.justification)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    decision_summary = {
        "decision": result.decision,
        "justification": result.justification,
        "bias_flagged": result.bias_check.flagged,
    }
    _store.update_status(candidate_id, result.decision, decision_summary)

    return DecideResponse(
        candidate_id=candidate_id,
        decision=result.decision,
        bias_check={
            "flagged": result.bias_check.flagged,
            "flagged_phrases": [
                {"phrase": fp.phrase, "reason": fp.reason, "suggestion": fp.suggestion}
                for fp in result.bias_check.flagged_phrases
            ],
        },
    )
