"""
Candidates router.
POST /candidates/upload  — ingest a CV (PDF), redact PII, return blind profile
GET  /candidates         — list all stored blind profiles
"""
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
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


@router.get("/")
def list_candidates():
    return [
        {"candidate_id": c["id"], "redacted_text": c["redacted_text"]}
        for c in _candidates.values()
    ]
