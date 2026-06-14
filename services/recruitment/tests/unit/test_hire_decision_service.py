"""
Unit tests for HireDecisionService.
Run: pytest services/recruitment/tests/unit/test_hire_decision_service.py -v
"""
import pytest
from shared.bias_analyzer.bias_analyzer import BiasAnalyzer
from app.services.hire_decision import HireDecisionService
from app.models import HireDecision


@pytest.fixture
def service():
    return HireDecisionService(bias_analyzer=BiasAnalyzer())


class TestValidDecisions:
    def test_hired_decision_returns_hire_decision(self, service):
        result = service.record(1, "hired", "Strong technical skills and clear communication.")
        assert isinstance(result, HireDecision)

    def test_rejected_decision_returns_hire_decision(self, service):
        result = service.record(1, "rejected", "Does not meet the required SQL criteria.")
        assert isinstance(result, HireDecision)

    def test_result_preserves_candidate_id(self, service):
        result = service.record(42, "hired", "Excellent candidate.")
        assert result.candidate_id == 42

    def test_result_preserves_decision(self, service):
        result = service.record(1, "rejected", "Not a match for this role.")
        assert result.decision == "rejected"

    def test_result_preserves_justification(self, service):
        justification = "Strong Python and SQL skills demonstrated in the assessment."
        result = service.record(1, "hired", justification)
        assert result.justification == justification


class TestValidation:
    def test_invalid_decision_raises(self, service):
        with pytest.raises(ValueError, match="decision"):
            service.record(1, "maybe", "Looks okay.")

    def test_empty_decision_raises(self, service):
        with pytest.raises(ValueError, match="decision"):
            service.record(1, "", "Some justification.")

    def test_empty_justification_raises(self, service):
        with pytest.raises(ValueError, match="justification"):
            service.record(1, "hired", "")

    def test_whitespace_only_justification_raises(self, service):
        with pytest.raises(ValueError, match="justification"):
            service.record(1, "hired", "   ")

    def test_nonexistent_decision_value_raises(self, service):
        with pytest.raises(ValueError, match="decision"):
            service.record(1, "pending", "Still thinking.")


class TestBiasCheck:
    def test_clean_justification_is_not_flagged(self, service):
        result = service.record(1, "hired", "Demonstrated strong Python skills and clear thinking.")
        assert result.bias_check.flagged is False

    def test_biased_justification_is_flagged(self, service):
        result = service.record(1, "rejected", "Not enough of a rockstar for this team.")
        assert result.bias_check.flagged is True

    def test_biased_justification_includes_flagged_phrase(self, service):
        result = service.record(1, "rejected", "We need a ninja, not a generalist.")
        phrases = [fp.phrase for fp in result.bias_check.flagged_phrases]
        assert "ninja" in phrases

    def test_bias_check_is_rule_based_not_ai(self, service):
        result = service.record(1, "hired", "Strong performer with good communication.")
        assert result.bias_check.ai_used is False

    def test_multiple_biased_phrases_all_flagged(self, service):
        result = service.record(1, "rejected", "Not a culture fit and lacks the rockstar attitude.")
        phrases = [fp.phrase for fp in result.bias_check.flagged_phrases]
        assert "culture fit" in phrases
        assert "rockstar" in phrases

    def test_flagged_phrase_includes_suggestion(self, service):
        result = service.record(1, "rejected", "Candidate is not a culture fit.")
        assert result.bias_check.flagged_phrases[0].suggestion != ""
