"""
Skills assessment service — scores candidates against weighted criteria.
No free-text gut-feel fields. Every score is explicit and auditable.
"""
from dataclasses import dataclass, field
from shared.base.service import BaseService


@dataclass
class AssessmentCriteria:
    name: str
    weight: float
    required: bool


@dataclass
class CandidateScore:
    total_score: float
    breakdown: dict = field(default_factory=dict)


class SkillsAssessmentService(BaseService):
    SCORE_MIN = 0
    SCORE_MAX = 10
    WEIGHT_TOLERANCE = 0.01

    def score(
        self,
        candidate_skills: dict[str, float],
        criteria: list[AssessmentCriteria],
    ) -> CandidateScore:
        self._validate_criteria(criteria)
        self._validate_scores(candidate_skills)
        self._validate_required_skills(candidate_skills, criteria)

        breakdown = {}
        total = 0.0
        for criterion in criteria:
            raw_score = candidate_skills.get(criterion.name, 0)
            breakdown[criterion.name] = raw_score
            total += raw_score * criterion.weight

        return CandidateScore(total_score=round(total, 4), breakdown=breakdown)

    def _validate_criteria(self, criteria: list[AssessmentCriteria]) -> None:
        if not criteria:
            raise ValueError("criteria list cannot be empty")

        names = [c.name for c in criteria]
        if len(names) != len(set(names)):
            raise ValueError("duplicate criteria names found — each skill must appear once")

        for c in criteria:
            if c.weight <= 0:
                raise ValueError(
                    f"criterion '{c.name}' has invalid weight {c.weight} — must be > 0"
                )

        total_weight = sum(c.weight for c in criteria)
        if abs(total_weight - 1.0) > self.WEIGHT_TOLERANCE:
            raise ValueError(
                f"criteria weights must sum to 1.0, got {total_weight:.4f}"
            )

    def _validate_scores(self, candidate_skills: dict[str, float]) -> None:
        for skill, score in candidate_skills.items():
            if not (self.SCORE_MIN <= score <= self.SCORE_MAX):
                raise ValueError(
                    f"Score for '{skill}' must be between 0 and 10, got {score}"
                )

    def _validate_required_skills(
        self,
        candidate_skills: dict[str, float],
        criteria: list[AssessmentCriteria],
    ) -> None:
        missing = [
            c.name for c in criteria
            if c.required and c.name not in candidate_skills
        ]
        if missing:
            raise ValueError(f"Missing required skills: {', '.join(missing)}")
