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