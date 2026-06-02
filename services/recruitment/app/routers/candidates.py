"""
Candidates router.
POST /candidates/upload  — ingest a CV (PDF), redact PII, return blind profile
GET  /candidates         — list all stored blind profiles
POST /candidates/assess  — score a candidate against weighted criteria
"""
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel, Field
from shared.document_parser.pdf_parser import PDFParser
from shared.document_parser.pii_redactor import PIIRedactor
from app.services.skills_assessment import SkillsAssessmentService, AssessmentCriteria

router = APIRouter(prefix="/candidates", tags=["candidates"])

_pdf_parser = PDFParser()
_redactor = PIIRedactor()
_assessment_service = SkillsAssessmentService()

# ── in-memory store (PII map never leaves the server) ────────────────────────
_candidates: dict[int, dict] = {}
_next_id = 1

ALLOWED_CONTENT_TYPES = {"application/pdf"}


# ── schemas ───────────────────────────────────────────────────────────────────

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


# ── routes ────────────────────────────────────────────────────────────────────

@router.post("/upload")
async def upload_candidate(file: UploadFile = File(...)):
    global _next_id

    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    raw = await file.read()

    try:
        text = _pdf_parser.extract_text_from_bytes(raw)
    except Exception:
        text = ""

    redacted_text, pii_map = _redactor.redact(text)

    candidate_id = _next_id
    _candidates[candidate_id] = {
        "id": candidate_id,
        "redacted_text": redacted_text,
        "_pii_map": pii_map,   # never returned to client
    }
    _next_id += 1

    return {"candidate_id": candidate_id, "redacted_text": redacted_text}


@router.get("")
def list_candidates():
    return [
        {"candidate_id": c["id"], "redacted_text": c["redacted_text"]}
        for c in _candidates.values()
    ]


@router.post("/assess", response_model=AssessResponse)
def assess_candidate(body: AssessRequest):
    criteria = [
        AssessmentCriteria(
            name=c["name"],
            weight=c["weight"],
            required=c["required"],
        )
        for c in body.criteria
    ]

    try:
        result = _assessment_service.score(body.scores, criteria)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    return AssessResponse(total_score=result.total_score, breakdown=result.breakdown)
