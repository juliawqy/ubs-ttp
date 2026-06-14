"""
Recruitment domain models shared across router and service layers.
"""
from dataclasses import dataclass, field


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
