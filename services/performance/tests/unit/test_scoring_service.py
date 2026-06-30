"""
Unit tests for PerformanceScoringService.
Run: pytest services/performance/tests/unit/test_scoring_service.py -v
"""
import pytest
from app.models import CriterionScore
from app.services.scoring import PerformanceScoringService


@pytest.fixture
def service():
    return PerformanceScoringService()


class TestScore:
    def test_single_criterion_breakdown(self, service):
        breakdown = service.score([CriterionScore(criterion="communication", score=4)])
        assert breakdown.per_criterion == {"communication": 4}

    def test_single_criterion_average_equals_its_score(self, service):
        breakdown = service.score([CriterionScore(criterion="communication", score=4)])
        assert breakdown.average == 4.0

    def test_multiple_criteria_breakdown_has_one_entry_each(self, service):
        breakdown = service.score([
            CriterionScore(criterion="technical_skill", score=5),
            CriterionScore(criterion="communication", score=3),
        ])
        assert breakdown.per_criterion == {"technical_skill": 5, "communication": 3}

    def test_average_is_mechanically_derived_from_scores(self, service):
        breakdown = service.score([
            CriterionScore(criterion="technical_skill", score=5),
            CriterionScore(criterion="communication", score=3),
        ])
        assert breakdown.average == 4.0

    def test_average_is_rounded_to_two_decimal_places(self, service):
        breakdown = service.score([
            CriterionScore(criterion="technical_skill", score=5),
            CriterionScore(criterion="communication", score=4),
            CriterionScore(criterion="collaboration", score=4),
        ])
        assert breakdown.average == 4.33

    def test_breakdown_has_no_overall_field_other_than_average(self, service):
        # Guard against regressions that reintroduce a free-text/gut-feel
        # "overall rating" field instead of the computed average.
        breakdown = service.score([CriterionScore(criterion="growth", score=2)])
        assert set(vars(breakdown).keys()) == {"per_criterion", "average"}


class TestValidation:
    def test_empty_criteria_raises(self, service):
        with pytest.raises(ValueError, match="criteria"):
            service.score([])

    def test_unknown_criterion_raises(self, service):
        with pytest.raises(ValueError, match="unknown criterion"):
            service.score([CriterionScore(criterion="vibes", score=5)])

    def test_duplicate_criterion_raises(self, service):
        with pytest.raises(ValueError, match="duplicate criterion"):
            service.score([
                CriterionScore(criterion="growth", score=3),
                CriterionScore(criterion="growth", score=5),
            ])

    def test_score_below_range_raises(self, service):
        with pytest.raises(ValueError, match="between 1 and 5"):
            service.score([CriterionScore(criterion="growth", score=0)])

    def test_score_above_range_raises(self, service):
        with pytest.raises(ValueError, match="between 1 and 5"):
            service.score([CriterionScore(criterion="growth", score=6)])
