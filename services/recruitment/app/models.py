"""
Recruitment domain models shared across router and service layers.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from shared.bias_analyzer.models import BiasAnalysisResult


@dataclass
class AssessmentCriteria:
    """A single weighted scoring criterion for candidate assessment."""
    name: str
    weight: float
    required: bool


@dataclass
class CandidateScore:
    """Result of scoring a candidate against a set of criteria."""
    total_score: float
    breakdown: dict = field(default_factory=dict)


@dataclass
class HireDecision:
    """
    The outcome of a hiring decision together with a bias check on the
    written justification. Human-in-the-loop: system flags bias, manager decides.
    """
    candidate_id: int
    decision: str          # "hired" | "rejected"
    justification: str
    bias_check: BiasAnalysisResult
