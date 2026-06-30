"""
Performance domain models shared across router and service layers.
"""
from __future__ import annotations
from dataclasses import dataclass
from shared.bias_analyzer.models import BiasAnalysisResult

RUBRIC_CRITERIA: dict[str, str] = {
    "technical_skill": "Quality and depth of technical work",
    "communication": "Clarity and effectiveness of communication",
    "collaboration": "Effectiveness working with others",
    "ownership": "Accountability and follow-through on commitments",
    "growth": "Progress against development goals",
}

MIN_SCORE = 1
MAX_SCORE = 5


@dataclass
class CriterionScore:
    """One rubric dimension's score plus optional supporting comments."""
    criterion: str
    score: int
    comments: str = ""


@dataclass
class ScoreBreakdown:
    """
    Per-criterion scores plus a mechanically-derived average.

    The average is *computed* here from the structured scores -- it is
    never collected directly from a reviewer -- so there is no separate
    overall rating for halo/recency bias to creep into.
    """
    per_criterion: dict[str, int]
    average: float


@dataclass
class Review:
    """
    A submitted performance review: the rubric scores it was built from,
    the mechanically-derived breakdown, and a per-criterion bias check on
    whichever comments were non-empty.

    bias_checks is advisory only -- a flagged comment is surfaced to the
    reviewer for revision but never blocks the review from being recorded.
    The human stays in control of the final wording.
    """
    employee_id: str
    reviewer_id: str
    criteria: list[CriterionScore]
    score: ScoreBreakdown
    bias_checks: dict[str, BiasAnalysisResult]


@dataclass
class FeedbackEntry:
    """
    One rater's free-text 360 feedback about an employee.

    rater_id is retained here only so FeedbackService can block a second
    submission from the same rater about the same employee -- it is never
    copied into AnonymisedFeedback, the only thing ever returned to a caller.
    """
    employee_id: str
    rater_id: str
    comments: str


@dataclass
class AnonymisedFeedback:
    """
    Aggregated 360 feedback for one employee: every comment plus a count.

    No rater_id field exists here at all -- by construction, not by
    filtering -- so there is nothing to accidentally leak.
    """
    employee_id: str
    comments: list[str]
    count: int
