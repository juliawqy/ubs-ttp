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


