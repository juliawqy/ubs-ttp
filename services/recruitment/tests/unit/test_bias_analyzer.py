"""
Unit tests for BiasAnalyzer (rule-based).
Run: pytest services/recruitment/tests/unit/test_bias_analyzer.py -v
"""

import pytest
from shared.bias_analyzer.bias_analyzer import BiasAnalyzer
from shared.bias_analyzer.models import BiasAnalysisResult


@pytest.fixture
def analyzer():
    return BiasAnalyzer()  


class TestCleanText:
    def test_clean_job_posting_returns_not_flagged(self, analyzer):
        text = "We are looking for an experienced Python engineer to join our team."
        result = analyzer.analyse_rule_based(text)
        assert result.flagged is False
        assert result.flagged_phrases == []

    def test_result_is_bias_analysis_result_type(self, analyzer):
        result = analyzer.analyse_rule_based("Clean text.")
        assert isinstance(result, BiasAnalysisResult)

    def test_clean_result_has_ai_used_false(self, analyzer):
        result = analyzer.analyse_rule_based("Clean text.")
        assert result.ai_used is False


class TestFlaggedPatterns:
    @pytest.mark.parametrize("phrase,expected_in_result", [
        ("rockstar developer", "rockstar"),
        ("We want a ninja engineer", "ninja"),
        ("Must be a culture fit", "culture fit"),
        ("aggressive sales targets", "aggressive"),
        ("digital native preferred", "digital native"),
    ])
    def test_known_biased_phrase_is_flagged(self, analyzer, phrase, expected_in_result):
        result = analyzer.analyse_rule_based(phrase)
        assert result.flagged is True
        phrases = [f.phrase for f in result.flagged_phrases]
        assert expected_in_result in phrases

    def test_flagged_phrase_includes_reason(self, analyzer):
        result = analyzer.analyse_rule_based("Looking for a rockstar")
        assert len(result.flagged_phrases) == 1
        assert result.flagged_phrases[0].reason != ""

    def test_flagged_phrase_includes_suggestion(self, analyzer):
        result = analyzer.analyse_rule_based("Looking for a rockstar")
        assert result.flagged_phrases[0].suggestion != ""


class TestCaseInsensitivity:
    def test_uppercase_phrase_is_caught(self, analyzer):
        result = analyzer.analyse_rule_based("We need a ROCKSTAR")
        assert result.flagged is True

    def test_mixed_case_phrase_is_caught(self, analyzer):
        result = analyzer.analyse_rule_based("Must be a Culture Fit")
        assert result.flagged is True


class TestMultipleFlags:
    def test_multiple_biased_phrases_all_flagged(self, analyzer):
        text = "Looking for a rockstar ninja who is a culture fit and a digital native."
        result = analyzer.analyse_rule_based(text)
        assert result.flagged is True
        assert len(result.flagged_phrases) == 4

    def test_each_flagged_phrase_has_reason_and_suggestion(self, analyzer):
        text = "rockstar ninja culture fit"
        result = analyzer.analyse_rule_based(text)
        for fp in result.flagged_phrases:
            assert fp.reason != ""
            assert fp.suggestion != ""


class TestAIClientNotRequired:
    def test_analyse_rule_based_works_without_ai_client(self, analyzer):
        """Rule-based analysis must never require AI — no cost, no latency."""
        result = analyzer.analyse_rule_based("rockstar developer wanted")
        assert result.flagged is True

    def test_analyse_with_ai_raises_without_client(self, analyzer):
        """Calling AI analysis without an injected client must raise clearly."""
        import asyncio
        with pytest.raises(ValueError, match="AI client not configured"):
            asyncio.run(analyzer.analyse_with_ai("some text"))


class TestAnalyseMethod:
    """Tests for the primary analyse() method — AI-first with rule-based fallback."""

    def test_analyse_without_client_returns_rule_based(self):
        analyzer = BiasAnalyzer()
        result = analyzer.analyse("rockstar developer")
        assert result.flagged is True
        assert result.ai_used is False

    def test_analyse_without_client_clean_text_not_flagged(self):
        analyzer = BiasAnalyzer()
        result = analyzer.analyse("Clear and effective communicator.")
        assert result.flagged is False
        assert result.ai_used is False

    def test_analyse_with_ai_client_calls_analyze_bias(self):
        from unittest.mock import MagicMock
        mock_client = MagicMock()
        mock_client.analyze_bias.return_value = {
            "flagged": False, "phrases": [], "overall_suggestion": None
        }
        analyzer = BiasAnalyzer(ai_client=mock_client)
        analyzer.analyse("some text")
        mock_client.analyze_bias.assert_called_once()

    def test_analyse_with_ai_client_sets_ai_used_true(self):
        from unittest.mock import MagicMock
        mock_client = MagicMock()
        mock_client.analyze_bias.return_value = {
            "flagged": False, "phrases": [], "overall_suggestion": None
        }
        analyzer = BiasAnalyzer(ai_client=mock_client)
        result = analyzer.analyse("some text")
        assert result.ai_used is True

    def test_analyse_ai_success_returns_flagged_phrases(self):
        from unittest.mock import MagicMock
        mock_client = MagicMock()
        mock_client.analyze_bias.return_value = {
            "flagged": True,
            "phrases": [{"phrase": "rockstar", "reason": "gendered", "suggestion": "high performer"}],
            "overall_suggestion": None,
        }
        analyzer = BiasAnalyzer(ai_client=mock_client)
        result = analyzer.analyse("rockstar developer")
        assert result.flagged is True
        assert any(fp.phrase == "rockstar" for fp in result.flagged_phrases)

    def test_analyse_falls_back_to_rule_based_on_ai_exception(self):
        from unittest.mock import MagicMock
        mock_client = MagicMock()
        mock_client.analyze_bias.side_effect = RuntimeError("API unavailable")
        analyzer = BiasAnalyzer(ai_client=mock_client)
        result = analyzer.analyse("rockstar developer")
        # Falls back — still flags the phrase via rule-based
        assert result.flagged is True
        assert result.ai_used is False

    def test_analyse_fallback_does_not_raise(self):
        from unittest.mock import MagicMock
        mock_client = MagicMock()
        mock_client.analyze_bias.side_effect = Exception("unexpected error")
        analyzer = BiasAnalyzer(ai_client=mock_client)
        # Must not propagate the exception
        result = analyzer.analyse("Clean text.")
        assert result is not None

class TestNationalityDiscriminationFlags:
    """Nationality/origin discrimination must be caught by the rule-based analyser."""

    def test_only_nationality_applicants_allowed_is_flagged(self, analyzer):
        result = analyzer.analyse_rule_based("only russian applicants allowed")
        assert result.flagged is True

    def test_only_nationality_applicants_phrase_appears_in_result(self, analyzer):
        result = analyzer.analyse_rule_based("only russian applicants allowed")
        # At least one flagged phrase must mention restriction of applicants
        phrases = " ".join(fp.phrase for fp in result.flagged_phrases).lower()
        assert "only" in phrases or "applicant" in phrases

    def test_no_foreigners_is_flagged(self, analyzer):
        result = analyzer.analyse_rule_based("No foreigners need apply for this role.")
        assert result.flagged is True

    def test_no_immigrants_is_flagged(self, analyzer):
        result = analyzer.analyse_rule_based("We do not accept applications from immigrants.")
        assert result.flagged is True

    def test_local_candidates_only_is_flagged(self, analyzer):
        result = analyzer.analyse_rule_based("Local candidates only, please.")
        assert result.flagged is True

    def test_locals_only_is_flagged(self, analyzer):
        result = analyzer.analyse_rule_based("Locals only.")
        assert result.flagged is True

    def test_only_us_citizens_is_flagged(self, analyzer):
        result = analyzer.analyse_rule_based("This role is open to US citizens only.")
        assert result.flagged is True

    def test_nationality_discrimination_flag_includes_reason(self, analyzer):
        result = analyzer.analyse_rule_based("only russian applicants allowed")
        assert result.flagged_phrases[0].reason != ""

    def test_nationality_discrimination_flag_includes_suggestion(self, analyzer):
        result = analyzer.analyse_rule_based("only russian applicants allowed")
        assert result.flagged_phrases[0].suggestion != ""

    def test_diverse_welcoming_text_not_flagged(self, analyzer):
        result = analyzer.analyse_rule_based(
            "We welcome applications from candidates of all backgrounds and nationalities."
        )
        assert result.flagged is False

    def test_nationality_check_case_insensitive(self, analyzer):
        result = analyzer.analyse_rule_based("Only RUSSIAN Applicants allowed")
        assert result.flagged is True
