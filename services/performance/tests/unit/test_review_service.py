"""
Unit tests for ReviewService.
Run: pytest services/performance/tests/unit/test_review_service.py -v
"""
import pytest
from shared.bias_analyzer.bias_analyzer import BiasAnalyzer
from app.models import CriterionScore, Review
from app.services.review import ReviewService
from app.services.scoring import PerformanceScoringService


@pytest.fixture
def service():
    return ReviewService(bias_analyzer=BiasAnalyzer(), scoring_service=PerformanceScoringService())


class TestSubmit:
    def test_returns_review_instance(self, service):
        result = service.submit("emp-1", "mgr-1", [CriterionScore(criterion="communication", score=4)])
        assert isinstance(result, Review)

    def test_preserves_employee_id(self, service):
        result = service.submit("emp-1", "mgr-1", [CriterionScore(criterion="communication", score=4)])
        assert result.employee_id == "emp-1"

    def test_preserves_reviewer_id(self, service):
        result = service.submit("emp-1", "mgr-1", [CriterionScore(criterion="communication", score=4)])
        assert result.reviewer_id == "mgr-1"

    def test_preserves_criteria(self, service):
        criteria = [CriterionScore(criterion="communication", score=4)]
        result = service.submit("emp-1", "mgr-1", criteria)
        assert result.criteria == criteria

    def test_score_breakdown_matches_scoring_service_output(self, service):
        criteria = [
            CriterionScore(criterion="technical_skill", score=5),
            CriterionScore(criterion="communication", score=3),
        ]
        result = service.submit("emp-1", "mgr-1", criteria)
        assert result.score.average == 4.0
        assert result.score.per_criterion == {"technical_skill": 5, "communication": 3}


class TestValidation:
    def test_empty_employee_id_raises(self, service):
        with pytest.raises(ValueError, match="employee_id"):
            service.submit("", "mgr-1", [CriterionScore(criterion="communication", score=4)])

    def test_whitespace_only_employee_id_raises(self, service):
        with pytest.raises(ValueError, match="employee_id"):
            service.submit("   ", "mgr-1", [CriterionScore(criterion="communication", score=4)])

    def test_empty_reviewer_id_raises(self, service):
        with pytest.raises(ValueError, match="reviewer_id"):
            service.submit("emp-1", "", [CriterionScore(criterion="communication", score=4)])

    def test_whitespace_only_reviewer_id_raises(self, service):
        with pytest.raises(ValueError, match="reviewer_id"):
            service.submit("emp-1", "   ", [CriterionScore(criterion="communication", score=4)])

    def test_invalid_criterion_propagates_from_scoring_service(self, service):
        # ReviewService delegates rubric validation to PerformanceScoringService
        # rather than duplicating the rule (DRY) -- this confirms it's wired in.
        with pytest.raises(ValueError, match="unknown criterion"):
            service.submit("emp-1", "mgr-1", [CriterionScore(criterion="vibes", score=5)])

    def test_empty_criteria_propagates_from_scoring_service(self, service):
        with pytest.raises(ValueError, match="criteria"):
            service.submit("emp-1", "mgr-1", [])

    def test_out_of_range_score_propagates_from_scoring_service(self, service):
        with pytest.raises(ValueError, match="between 1 and 5"):
            service.submit("emp-1", "mgr-1", [CriterionScore(criterion="growth", score=9)])


class TestBiasCheck:
    def test_clean_comment_is_not_flagged(self, service):
        criteria = [CriterionScore(criterion="communication", score=4, comments="Clear and concise in meetings.")]
        result = service.submit("emp-1", "mgr-1", criteria)
        assert result.bias_checks["communication"].flagged is False

    def test_biased_comment_is_flagged(self, service):
        criteria = [CriterionScore(criterion="technical_skill", score=5, comments="Total rockstar engineer.")]
        result = service.submit("emp-1", "mgr-1", criteria)
        assert result.bias_checks["technical_skill"].flagged is True

    def test_biased_comment_includes_flagged_phrase(self, service):
        criteria = [CriterionScore(criterion="collaboration", score=3, comments="Not a culture fit on the team.")]
        result = service.submit("emp-1", "mgr-1", criteria)
        phrases = [fp.phrase for fp in result.bias_checks["collaboration"].flagged_phrases]
        assert "culture fit" in phrases

    def test_empty_comment_is_not_bias_checked(self, service):
        criteria = [CriterionScore(criterion="growth", score=3, comments="")]
        result = service.submit("emp-1", "mgr-1", criteria)
        assert "growth" not in result.bias_checks

    def test_whitespace_only_comment_is_not_bias_checked(self, service):
        criteria = [CriterionScore(criterion="growth", score=3, comments="   ")]
        result = service.submit("emp-1", "mgr-1", criteria)
        assert "growth" not in result.bias_checks

    def test_default_comment_is_not_bias_checked(self, service):
        # CriterionScore.comments defaults to "" -- no comment, no bias check entry.
        criteria = [CriterionScore(criterion="growth", score=3)]
        result = service.submit("emp-1", "mgr-1", criteria)
        assert "growth" not in result.bias_checks

    def test_multiple_criteria_each_get_independent_bias_check(self, service):
        criteria = [
            CriterionScore(criterion="technical_skill", score=5, comments="Total rockstar."),
            CriterionScore(criterion="communication", score=4, comments="Clear and direct."),
        ]
        result = service.submit("emp-1", "mgr-1", criteria)
        assert result.bias_checks["technical_skill"].flagged is True
        assert result.bias_checks["communication"].flagged is False

    def test_bias_check_is_rule_based_not_ai(self, service):
        criteria = [CriterionScore(criterion="ownership", score=4, comments="Reliable and accountable.")]
        result = service.submit("emp-1", "mgr-1", criteria)
        assert result.bias_checks["ownership"].ai_used is False

    def test_bias_check_is_advisory_not_blocking(self, service):
        # Human stays in control: a flagged comment must not prevent the
        # review from being recorded.
        criteria = [CriterionScore(criterion="technical_skill", score=5, comments="Such a ninja.")]
        result = service.submit("emp-1", "mgr-1", criteria)
        assert isinstance(result, Review)
        assert result.bias_checks["technical_skill"].flagged is True


class TestDefaults:
    def test_can_be_constructed_with_no_arguments(self):
        # DIP: both collaborators are optional and default to real,
        # rule-based implementations -- mirrors JobPostingsService.
        service = ReviewService()
        result = service.submit("emp-1", "mgr-1", [CriterionScore(criterion="communication", score=4)])
        assert isinstance(result, Review)

    def test_default_bias_analyzer_still_flags_biased_language(self):
        service = ReviewService()
        criteria = [CriterionScore(criterion="technical_skill", score=5, comments="Such a ninja.")]
        result = service.submit("emp-1", "mgr-1", criteria)
        assert result.bias_checks["technical_skill"].flagged is True
