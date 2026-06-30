"""
Performance scoring service -- scores an employee against the predefined
rubric only. No field anywhere accepts a single subjective "overall" score;
the average returned here is computed from the structured per-criterion
scores, never collected directly from a reviewer.

Structured, named criteria force the rater to justify each dimension
separately, which is what guards against halo bias (one strong or weak
impression colouring every dimension) -- there is simply no single rating
for a halo to spread across.
"""
from shared.base.service import BaseService
from app.models import RUBRIC_CRITERIA, MIN_SCORE, MAX_SCORE, CriterionScore, ScoreBreakdown


class PerformanceScoringService(BaseService):
    """Computes a per-criterion score breakdown -- never a single blended rating."""

    def score(self, criteria: list[CriterionScore]) -> ScoreBreakdown:
        """
        Raises:
            ValueError: if criteria is empty, contains an unknown or
                        duplicate criterion, or a score outside [1, 5].
        """
        self._validate(criteria)
        per_criterion = {c.criterion: c.score for c in criteria}
        average = round(sum(per_criterion.values()) / len(per_criterion), 2)
        return ScoreBreakdown(per_criterion=per_criterion, average=average)

    # -- internals ------------------------------------------------------------

    def _validate(self, criteria: list[CriterionScore]) -> None:
        if not criteria:
            raise ValueError("criteria cannot be empty")

        seen: set[str] = set()
        for c in criteria:
            if c.criterion not in RUBRIC_CRITERIA:
                raise ValueError(
                    f"unknown criterion: '{c.criterion}' (expected one of {sorted(RUBRIC_CRITERIA)})"
                )
            if c.criterion in seen:
                raise ValueError(f"duplicate criterion: '{c.criterion}'")
            seen.add(c.criterion)

            if not MIN_SCORE <= c.score <= MAX_SCORE:
                raise ValueError(
                    f"score for '{c.criterion}' must be between {MIN_SCORE} and {MAX_SCORE}"
                )
