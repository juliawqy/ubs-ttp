"""Data models for bias analysis results."""
from pydantic import BaseModel


class FlaggedPhrase(BaseModel):
    phrase: str
    reason: str
    suggestion: str


class BiasAnalysisResult(BaseModel):
    flagged: bool
    flagged_phrases: list[FlaggedPhrase]
    overall_suggestion: str | None = None
    # AI was used to produce this result — logged for audit
    ai_used: bool = False
