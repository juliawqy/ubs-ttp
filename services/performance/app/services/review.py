"""
Review service -- validates a structured performance review submission and
runs an advisory bias check on the free-text comments before save.

Composes PerformanceScoringService for the score breakdown rather than
recomputing rubric validation/averaging here (DRY, single source of truth
for "what counts as a valid score"). Mirrors recruitment's
JobPostingsService/HireDecisionService DIP pattern: the bias analyzer is
injected and defaults to the rule-based implementation, so callers can swap
in a different analyzer (e.g. an AI-backed one) without changing this class.

Human-in-the-loop: a flagged comment is surfaced on the result for the
reviewer to revise, but it never blocks the review from being recorded.
"""
from shared.base.service import BaseService
from shared.bias_analyzer.bias_analyzer import BiasAnalyzer
from app.models import CriterionScore, Review
from app.services.scoring import PerformanceScoringService


class ReviewService(BaseService):
    """
    Validates and records a performance review.

    Args:
        bias_analyzer: injected BiasAnalyzer instance; defaults to a fresh
                        rule-based BiasAnalyzer() (no AI cost).
        scoring_service: injected PerformanceScoringService instance;
                          defaults to a fresh PerformanceScoringService().
    """

    def __init__(
        self,
        bias_analyzer: BiasAnalyzer | None = None,
        scoring_service: PerformanceScoringService | None = None,
    ):
        self._bias_analyzer = bias_analyzer or BiasAnalyzer()
        self._scoring_service = scoring_service or PerformanceScoringService()

    def submit(self, employee_id: str, reviewer_id: str, criteria: list[CriterionScore]) -> Review:
        """
        Validate the submission, score it, and run an advisory bias check
        on every non-empty comment.

        Raises:
            ValueError: if employee_id/reviewer_id is empty, or if criteria
                        is empty/invalid (delegated to PerformanceScoringService).
        """
        self._validate_ids(employee_id, reviewer_id)

        # Rubric validation + averaging lives in one place only.
        score = self._scoring_service.score(criteria)

        bias_checks = {
            c.criterion: self._bias_analyzer.analyse(c.comments)
            for c in criteria
            if c.comments and c.comments.strip()
        }

        return Review(
            employee_id=employee_id,
            reviewer_id=reviewer_id,
            criteria=criteria,
            score=score,
            bias_checks=bias_checks,
        )

    # -- internals ------------------------------------------------------------

    def _validate_ids(self, employee_id: str, reviewer_id: str) -> None:
        if not employee_id or not employee_id.strip():
            raise ValueError("employee_id cannot be empty")
        if not reviewer_id or not reviewer_id.strip():
            raise ValueError("reviewer_id cannot be empty")
