"""
Assistant router.
POST /assistant/analyze -- analyse any HR text (job ad, review, feedback)
                           for biased language via Claude AI.
                           Returns flagged phrases with category
                           (gender/age/ethnicity/ability/socioeconomic/general),
                           severity score (1-3), and neutral replacement suggestions.
                           Falls back to rule-based analysis if Claude is unavailable.
"""
from typing import Annotated
from fastapi import APIRouter, Depends
from pydantic import BaseModel, field_validator
from shared.ai_client.factory import make_ai_client
from app.models import AnalysisResult
from app.services.bias_classifier import BiasDetectionService

router = APIRouter(prefix="/assistant", tags=["assistant"])


# -- DI -----------------------------------------------------------------------

def get_service() -> BiasDetectionService:
    """
    FastAPI dependency — always injects a real ClaudeClient so the endpoint
    makes genuine AI calls. Falls back gracefully inside BiasDetectionService
    if the API is unavailable (key missing, network error, quota, etc.).
    Tests override this via app.dependency_overrides[get_service].
    """
    return BiasDetectionService(ai_client=make_ai_client())


# -- schemas ------------------------------------------------------------------

class AnalyzeRequest(BaseModel):
    text: str
    context: str = "general"

    @field_validator("text")
    @classmethod
    def text_must_not_be_blank(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("text must not be empty")
        return v


class EnrichedPhraseOut(BaseModel):
    phrase: str
    reason: str
    suggestion: str
    category: str
    severity: int


class AnalyzeResponse(BaseModel):
    flagged: bool
    flagged_phrases: list[EnrichedPhraseOut]
    overall_suggestion: str | None
    ai_used: bool


# -- routes -------------------------------------------------------------------

@router.post("/analyze", response_model=AnalyzeResponse)
def analyze(
    body: AnalyzeRequest,
    svc: Annotated[BiasDetectionService, Depends(get_service)],
) -> AnalyzeResponse:
    """TTP-24: Analyse HR text for biased language using Claude AI with rule-based fallback."""
    result: AnalysisResult = svc.analyze(body.text, body.context)
    return AnalyzeResponse(
        flagged=result.flagged,
        flagged_phrases=[
            EnrichedPhraseOut(
                phrase=p.phrase,
                reason=p.reason,
                suggestion=p.suggestion,
                category=p.category.value,
                severity=p.severity,
            )
            for p in result.flagged_phrases
        ],
        overall_suggestion=result.overall_suggestion,
        ai_used=result.ai_used,
    )
