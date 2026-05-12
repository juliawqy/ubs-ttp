"""
Unit tests for SkillsAssessment.
Run: pytest services/recruitment/tests/unit/test_skills_assessment.py -v
"""
import pytest
from app.services.skills_assessment import SkillsAssessmentService, AssessmentCriteria, CandidateScore


@pytest.fixture
def criteria():
    """Standard criteria set for a Python backend role."""
    return [
        AssessmentCriteria(name="python", weight=0.4, required=True),
        AssessmentCriteria(name="sql", weight=0.3, required=True),
        AssessmentCriteria(name="communication", weight=0.2, required=False),
        AssessmentCriteria(name="system_design", weight=0.1, required=False),
    ]


@pytest.fixture
def service():
    return SkillsAssessmentService()


class TestScoring:
    def test_perfect_score_returns_100(self, service, criteria):
        candidate_skills = {
            "python": 10, "sql": 10, "communication": 10, "system_design": 10
        }
        result = service.score(candidate_skills, criteria)
        assert result.total_score == pytest.approx(10.0)

    def test_zero_score_returns_0(self, service, criteria):
        candidate_skills = {
            "python": 0, "sql": 0, "communication": 0, "system_design": 0
        }
        result = service.score(candidate_skills, criteria)
        assert result.total_score == pytest.approx(0.0)

    def test_weighted_score_calculated_correctly(self, service, criteria):
        # python=10 (weight 0.4), sql=5 (weight 0.3), others=0
        # expected = 10*0.4 + 5*0.3 + 0 + 0 = 4.0 + 1.5 = 5.5
        candidate_skills = {"python": 10, "sql": 5, "communication": 0, "system_design": 0}
        result = service.score(candidate_skills, criteria)
        assert result.total_score == pytest.approx(5.5)

    def test_result_is_candidate_score_type(self, service, criteria):
        result = service.score({"python": 5, "sql": 5}, criteria)
        assert isinstance(result, CandidateScore)

    def test_score_includes_per_criteria_breakdown(self, service, criteria):
        candidate_skills = {"python": 8, "sql": 6, "communication": 7, "system_design": 5}
        result = service.score(candidate_skills, criteria)
        assert "python" in result.breakdown
        assert "sql" in result.breakdown


class TestRequiredCriteria:
    def test_missing_required_skill_raises(self, service, criteria):
        """Candidates missing required skills must not receive a score."""
        with pytest.raises(ValueError, match="required"):
            service.score({"communication": 8}, criteria)

    def test_missing_optional_skill_defaults_to_zero(self, service, criteria):
        """Optional skills not provided count as zero, not an error."""
        result = service.score({"python": 8, "sql": 7}, criteria)
        assert result.breakdown.get("communication", 0) == 0
        assert result.breakdown.get("system_design", 0) == 0


class TestEdgeCases:
    def test_scores_outside_range_raises(self, service, criteria):
        with pytest.raises(ValueError, match="0.*10"):
            service.score({"python": 11, "sql": 5}, criteria)

    def test_negative_score_raises(self, service, criteria):
        with pytest.raises(ValueError, match="0.*10"):
            service.score({"python": -1, "sql": 5}, criteria)

    def test_empty_criteria_raises(self, service):
        with pytest.raises(ValueError, match="criteria"):
            service.score({"python": 5}, [])

    def test_weights_not_summing_to_one_raises(self, service):
        bad_criteria = [
            AssessmentCriteria(name="python", weight=0.5, required=True),
            AssessmentCriteria(name="sql", weight=0.8, required=True),
        ]
        with pytest.raises(ValueError, match="weight"):
            service.score({"python": 5, "sql": 5}, bad_criteria)


class TestBoundaryValues:
    def test_score_of_exactly_0_is_valid(self, service, criteria):
        """0 is a valid score — candidate attempted but scored nothing."""
        result = service.score({"python": 0, "sql": 0}, criteria)
        assert result.total_score == pytest.approx(0.0)

    def test_score_of_exactly_10_is_valid(self, service, criteria):
        result = service.score({"python": 10, "sql": 10}, criteria)
        assert result.total_score is not None

    def test_single_criterion_with_weight_1(self, service):
        """A rubric with just one criterion summing to 1.0 is valid."""
        single = [AssessmentCriteria(name="python", weight=1.0, required=True)]
        result = service.score({"python": 7}, single)
        assert result.total_score == pytest.approx(7.0)

    def test_weights_summing_to_1_within_float_tolerance(self, service):
        """Floating point arithmetic can produce 0.9999... — should still be accepted."""
        criteria = [
            AssessmentCriteria(name="a", weight=0.1, required=True),
            AssessmentCriteria(name="b", weight=0.2, required=True),
            AssessmentCriteria(name="c", weight=0.3, required=True),
            AssessmentCriteria(name="d", weight=0.4, required=True),
        ]
        result = service.score({"a": 5, "b": 5, "c": 5, "d": 5}, criteria)
        assert result.total_score is not None

    def test_all_optional_criteria_scored_zero(self, service, criteria):
        """All optional skills at zero with required skills present is valid."""
        result = service.score(
            {"python": 5, "sql": 5, "communication": 0, "system_design": 0},
            criteria,
        )
        assert result.total_score == pytest.approx(5 * 0.4 + 5 * 0.3)


class TestAdditionalNegative:
    def test_duplicate_criteria_names_raises(self, service):
        """Two criteria with the same name is a misconfigured rubric."""
        duplicate = [
            AssessmentCriteria(name="python", weight=0.5, required=True),
            AssessmentCriteria(name="python", weight=0.5, required=True),
        ]
        with pytest.raises(ValueError, match="duplicate"):
            service.score({"python": 5}, duplicate)

    def test_zero_weight_criterion_raises(self, service):
        """A criterion with weight 0 is meaningless and indicates a config error."""
        bad = [
            AssessmentCriteria(name="python", weight=1.0, required=True),
            AssessmentCriteria(name="sql", weight=0.0, required=False),
        ]
        with pytest.raises(ValueError, match="weight"):
            service.score({"python": 5, "sql": 5}, bad)

    def test_negative_weight_raises(self, service):
        bad = [
            AssessmentCriteria(name="python", weight=1.2, required=True),
            AssessmentCriteria(name="sql", weight=-0.2, required=False),
        ]
        with pytest.raises(ValueError, match="weight"):
            service.score({"python": 5, "sql": 5}, bad)

    def test_float_score_just_above_max_raises(self, service, criteria):
        """10.001 should be rejected — not just integers outside range."""
        with pytest.raises(ValueError, match="0.*10"):
            service.score({"python": 10.001, "sql": 5}, criteria)

    def test_empty_skills_dict_with_required_criteria_raises(self, service, criteria):
        with pytest.raises(ValueError, match="required"):
            service.score({}, criteria)
