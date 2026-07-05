"""
Domain models for the AI Assistant service (TTP-24/25).

EnrichedFlaggedPhrase extends the shared FlaggedPhrase with category and
severity — fields specific to the assistant's richer output contract.
These are NOT in shared because only the assistant service exposes them.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum


class BiasCategory(str, Enum):
    """Category of bias detected in a phrase (TTP-25)."""
    gender = "gender"
    age = "age"
    ethnicity = "ethnicity"
    ability = "ability"
    socioeconomic = "socioeconomic"
    general = "general"

    @classmethod
    def from_str(cls, value: str) -> "BiasCategory":
        """Parse a string from AI response; unknown values fall back to 'general'."""
        try:
            return cls(value.lower())
        except (ValueError, AttributeError):
            return cls.general


@dataclass
class EnrichedFlaggedPhrase:
    """
    A flagged phrase enriched with bias category and severity score.
    Severity: 1 = low, 2 = medium, 3 = high.
    """
    phrase: str
    reason: str
    suggestion: str
    category: BiasCategory
    severity: int


@dataclass
class AnalysisResult:
    """
    Full result of a bias analysis request.
    Returned by BiasDetectionService and serialised by the router.
    """
    flagged: bool
    flagged_phrases: list[EnrichedFlaggedPhrase] = field(default_factory=list)
    overall_suggestion: str | None = None
    ai_used: bool = False
