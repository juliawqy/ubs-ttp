"""
Unit tests for BiasDetectionService (TTP-24/25).
Written before implementation — TDD.
Run: pytest services/ai-assistant/tests/unit/test_bias_detection_service.py -v
"""
import pytest
from unittest.mock import MagicMock
from app.services.bias_classifier import BiasDetectionService
from app.models import BiasCategory


# ── helpers ──────────────────────────────────────────────────────────────────

def _make_service(ai_client=None):
    return BiasDetectionService(ai_client=ai_client)


def _mock_ai_client(response: dict):
    """Return a mock client whose analyze_bias returns the given dict."""
    client = MagicMock()
    client.analyze_bias.return_value = response
    return client


def _ai_clean_response():
    return {"flagged": False, "phrases": [], "overall_suggestion": None}


def _ai_flagged_response():
    return {
        "flagged": True,
        "phrases": [
            {
                "phrase": "rockstar",
                "reason": "Gendered jargon",
                "suggestion": "high performer",
                "category": "gender",
                "severity": 2,
            }
        ],
        "overall_suggestion": "Revise to use neutral language.",
    }


# ── rule-based enrichment (no AI) ─────────────────────────────────────────────

class TestRuleBasedEnrichment:
    def test_clean_text_not_flagged(self):
        svc = _make_service()
        result = svc.analyze("Strong technical skills and clear communication.", "review")
        assert result.flagged is False

    def test_known_phrase_is_flagged(self):
        svc = _make_service()
        result = svc.analyze("We need a rockstar engineer.", "job_posting")
        assert result.flagged is True

    def test_flagged_phrase_text_preserved(self):
        svc = _make_service()
        result = svc.analyze("We need a rockstar engineer.", "job_posting")
        phrases = [p.phrase for p in result.flagged_phrases]
        assert "rockstar" in phrases

    def test_flagged_phrase_includes_category(self):
        svc = _make_service()
        result = svc.analyze("We need a rockstar engineer.", "job_posting")
        assert result.flagged_phrases[0].category is not None

    def test_flagged_phrase_category_is_valid_enum(self):
        svc = _make_service()
        result = svc.analyze("We need a rockstar engineer.", "job_posting")
        assert isinstance(result.flagged_phrases[0].category, BiasCategory)

    def test_rockstar_has_gender_category(self):
        svc = _make_service()
        result = svc.analyze("Total rockstar on the team.", "review")
        phrase = result.flagged_phrases[0]
        assert phrase.category == BiasCategory.gender

    def test_digital_native_has_age_category(self):
        svc = _make_service()
        result = svc.analyze("Must be a digital native.", "job_posting")
        phrase = result.flagged_phrases[0]
        assert phrase.category == BiasCategory.age

    def test_flagged_phrase_includes_severity(self):
        svc = _make_service()
        result = svc.analyze("We need a rockstar engineer.", "job_posting")
        assert result.flagged_phrases[0].severity is not None

    def test_severity_is_integer_1_to_3(self):
        svc = _make_service()
        result = svc.analyze("We need a rockstar engineer.", "job_posting")
        sev = result.flagged_phrases[0].severity
        assert isinstance(sev, int)
        assert 1 <= sev <= 3

    def test_multiple_phrases_all_enriched(self):
        svc = _make_service()
        result = svc.analyze("We want a ninja rockstar who is a digital native.", "job_posting")
        assert len(result.flagged_phrases) >= 3
        for phrase in result.flagged_phrases:
            assert phrase.category is not None
            assert phrase.severity is not None

    def test_phrase_includes_reason(self):
        svc = _make_service()
        result = svc.analyze("Looking for a ninja developer.", "job_posting")
        assert result.flagged_phrases[0].reason.strip()

    def test_phrase_includes_suggestion(self):
        svc = _make_service()
        result = svc.analyze("Looking for a ninja developer.", "job_posting")
        assert result.flagged_phrases[0].suggestion.strip()

    def test_ai_used_is_false_without_client(self):
        svc = _make_service(ai_client=None)
        result = svc.analyze("Total rockstar.", "review")
        assert result.ai_used is False


# ── AI path ──────────────────────────────────────────────────────────────────

class TestAIPath:
    def test_ai_client_called_when_provided(self):
        mock_client = _mock_ai_client(_ai_clean_response())
        svc = _make_service(ai_client=mock_client)
        svc.analyze("Some text.", "review")
        mock_client.analyze_bias.assert_called_once()

    def test_ai_client_receives_text(self):
        mock_client = _mock_ai_client(_ai_clean_response())
        svc = _make_service(ai_client=mock_client)
        svc.analyze("Some text.", "review")
        call_kwargs = mock_client.analyze_bias.call_args
        assert "Some text." in str(call_kwargs)

    def test_ai_client_receives_context(self):
        mock_client = _mock_ai_client(_ai_clean_response())
        svc = _make_service(ai_client=mock_client)
        svc.analyze("Some text.", "job_posting")
        call_kwargs = mock_client.analyze_bias.call_args
        assert "job_posting" in str(call_kwargs)

    def test_ai_used_is_true_when_client_provided(self):
        mock_client = _mock_ai_client(_ai_clean_response())
        svc = _make_service(ai_client=mock_client)
        result = svc.analyze("Some text.", "review")
        assert result.ai_used is True

    def test_ai_flagged_phrase_present_in_result(self):
        mock_client = _mock_ai_client(_ai_flagged_response())
        svc = _make_service(ai_client=mock_client)
        result = svc.analyze("We need a rockstar.", "review")
        assert result.flagged is True
        phrases = [p.phrase for p in result.flagged_phrases]
        assert "rockstar" in phrases

    def test_ai_phrase_category_parsed(self):
        mock_client = _mock_ai_client(_ai_flagged_response())
        svc = _make_service(ai_client=mock_client)
        result = svc.analyze("We need a rockstar.", "review")
        phrase = next(p for p in result.flagged_phrases if p.phrase == "rockstar")
        assert phrase.category == BiasCategory.gender

    def test_ai_phrase_severity_parsed(self):
        mock_client = _mock_ai_client(_ai_flagged_response())
        svc = _make_service(ai_client=mock_client)
        result = svc.analyze("We need a rockstar.", "review")
        phrase = next(p for p in result.flagged_phrases if p.phrase == "rockstar")
        assert phrase.severity == 2

    def test_ai_overall_suggestion_returned(self):
        mock_client = _mock_ai_client(_ai_flagged_response())
        svc = _make_service(ai_client=mock_client)
        result = svc.analyze("We need a rockstar.", "review")
        assert result.overall_suggestion is not None

    def test_unknown_category_from_ai_defaults_to_general(self):
        response = {
            "flagged": True,
            "phrases": [{"phrase": "something", "reason": "r", "suggestion": "s",
                         "category": "unknown_type", "severity": 1}],
            "overall_suggestion": None,
        }
        mock_client = _mock_ai_client(response)
        svc = _make_service(ai_client=mock_client)
        result = svc.analyze("something", "review")
        assert result.flagged_phrases[0].category == BiasCategory.general


# ── fallback / resilience ─────────────────────────────────────────────────────

class TestFallback:
    def test_fallback_when_ai_raises(self):
        mock_client = MagicMock()
        mock_client.analyze_bias.side_effect = RuntimeError("API unavailable")
        svc = _make_service(ai_client=mock_client)
        # Should not raise — falls back to rule-based
        result = svc.analyze("Total rockstar.", "review")
        assert result is not None

    def test_fallback_result_still_flags_rule_based_phrases(self):
        mock_client = MagicMock()
        mock_client.analyze_bias.side_effect = RuntimeError("API unavailable")
        svc = _make_service(ai_client=mock_client)
        result = svc.analyze("Total rockstar.", "review")
        assert result.flagged is True

    def test_fallback_ai_used_is_false(self):
        mock_client = MagicMock()
        mock_client.analyze_bias.side_effect = RuntimeError("API unavailable")
        svc = _make_service(ai_client=mock_client)
        result = svc.analyze("Total rockstar.", "review")
        assert result.ai_used is False

    def test_fallback_clean_text_not_flagged(self):
        mock_client = MagicMock()
        mock_client.analyze_bias.side_effect = RuntimeError("API unavailable")
        svc = _make_service(ai_client=mock_client)
        result = svc.analyze("Clear and concise communication.", "review")
        assert result.flagged is False

    def test_no_ai_call_when_client_is_none(self):
        # No client — must not raise, must succeed via rule-based
        svc = _make_service(ai_client=None)
        result = svc.analyze("Clear communication.", "general")
        assert result is not None
        assert result.ai_used is False
