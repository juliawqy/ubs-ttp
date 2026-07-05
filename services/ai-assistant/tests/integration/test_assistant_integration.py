"""
Integration tests for the AI Assistant with mocked Claude responses (TTP-26).
Tests: correct response parsing, fallback when API unavailable.
Run: pytest services/ai-assistant/tests/integration/test_assistant_integration.py -v
"""
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from app.main import app
from app.services.bias_classifier import BiasDetectionService
from app.models import BiasCategory


# ── mock helpers ─────────────────────────────────────────────────────────────

def _make_mock_client(response: dict) -> MagicMock:
    client = MagicMock()
    client.analyze_bias.return_value = response
    return client


def _make_failing_client(exc: Exception = None) -> MagicMock:
    client = MagicMock()
    client.analyze_bias.side_effect = exc or RuntimeError("Claude API unavailable")
    return client


MOCK_CLAUDE_FLAGGED = {
    "flagged": True,
    "phrases": [
        {
            "phrase": "ninja",
            "reason": "Exclusionary jargon that can deter diverse candidates",
            "suggestion": "expert or specialist",
            "category": "gender",
            "severity": 2,
        },
        {
            "phrase": "young and dynamic",
            "reason": "Age-discriminatory language that excludes older workers",
            "suggestion": "energetic and adaptable",
            "category": "age",
            "severity": 3,
        },
    ],
    "overall_suggestion": "Use inclusive, skills-focused language throughout.",
}

MOCK_CLAUDE_CLEAN = {
    "flagged": False,
    "phrases": [],
    "overall_suggestion": None,
}


# ── mocked Claude responses ───────────────────────────────────────────────────

class TestMockedClaudeResponses:
    def test_mocked_flagged_response_sets_flagged_true(self):
        mock_client = _make_mock_client(MOCK_CLAUDE_FLAGGED)
        svc = BiasDetectionService(ai_client=mock_client)
        result = svc.analyze("We want a ninja and young and dynamic team member.", "job_posting")
        assert result.flagged is True

    def test_mocked_response_phrase_count_matches(self):
        mock_client = _make_mock_client(MOCK_CLAUDE_FLAGGED)
        svc = BiasDetectionService(ai_client=mock_client)
        result = svc.analyze("We want a ninja and young and dynamic team member.", "job_posting")
        assert len(result.flagged_phrases) == 2

    def test_mocked_phrase_text_parsed_correctly(self):
        mock_client = _make_mock_client(MOCK_CLAUDE_FLAGGED)
        svc = BiasDetectionService(ai_client=mock_client)
        result = svc.analyze("We want a ninja and young and dynamic team member.", "job_posting")
        phrases = [p.phrase for p in result.flagged_phrases]
        assert "ninja" in phrases
        assert "young and dynamic" in phrases

    def test_mocked_phrase_category_parsed_correctly(self):
        mock_client = _make_mock_client(MOCK_CLAUDE_FLAGGED)
        svc = BiasDetectionService(ai_client=mock_client)
        result = svc.analyze("We want a ninja.", "job_posting")
        ninja_phrase = next(p for p in result.flagged_phrases if p.phrase == "ninja")
        assert ninja_phrase.category == BiasCategory.gender

    def test_mocked_phrase_severity_parsed_correctly(self):
        mock_client = _make_mock_client(MOCK_CLAUDE_FLAGGED)
        svc = BiasDetectionService(ai_client=mock_client)
        result = svc.analyze("We want a ninja.", "job_posting")
        ninja_phrase = next(p for p in result.flagged_phrases if p.phrase == "ninja")
        assert ninja_phrase.severity == 2

    def test_mocked_age_phrase_has_age_category(self):
        mock_client = _make_mock_client(MOCK_CLAUDE_FLAGGED)
        svc = BiasDetectionService(ai_client=mock_client)
        result = svc.analyze("young and dynamic team", "job_posting")
        age_phrase = next(p for p in result.flagged_phrases if p.phrase == "young and dynamic")
        assert age_phrase.category == BiasCategory.age

    def test_mocked_overall_suggestion_returned(self):
        mock_client = _make_mock_client(MOCK_CLAUDE_FLAGGED)
        svc = BiasDetectionService(ai_client=mock_client)
        result = svc.analyze("We want a ninja.", "job_posting")
        assert result.overall_suggestion == "Use inclusive, skills-focused language throughout."

    def test_mocked_clean_response_not_flagged(self):
        mock_client = _make_mock_client(MOCK_CLAUDE_CLEAN)
        svc = BiasDetectionService(ai_client=mock_client)
        result = svc.analyze("Strong communicator with collaborative style.", "review")
        assert result.flagged is False

    def test_mocked_clean_response_empty_phrases(self):
        mock_client = _make_mock_client(MOCK_CLAUDE_CLEAN)
        svc = BiasDetectionService(ai_client=mock_client)
        result = svc.analyze("Strong communicator with collaborative style.", "review")
        assert result.flagged_phrases == []

    def test_ai_used_true_when_mock_client_provided(self):
        mock_client = _make_mock_client(MOCK_CLAUDE_CLEAN)
        svc = BiasDetectionService(ai_client=mock_client)
        result = svc.analyze("Some text.", "general")
        assert result.ai_used is True


# ── fallback: API unavailable ─────────────────────────────────────────────────

class TestFallbackBehaviour:
    def test_fallback_does_not_raise(self):
        failing = _make_failing_client()
        svc = BiasDetectionService(ai_client=failing)
        result = svc.analyze("Total rockstar.", "review")
        assert result is not None

    def test_fallback_still_catches_rule_based_flags(self):
        failing = _make_failing_client()
        svc = BiasDetectionService(ai_client=failing)
        result = svc.analyze("We need a rockstar ninja developer.", "job_posting")
        assert result.flagged is True

    def test_fallback_rule_based_phrases_have_category(self):
        failing = _make_failing_client()
        svc = BiasDetectionService(ai_client=failing)
        result = svc.analyze("We need a rockstar.", "job_posting")
        assert result.flagged_phrases[0].category is not None

    def test_fallback_ai_used_is_false(self):
        failing = _make_failing_client()
        svc = BiasDetectionService(ai_client=failing)
        result = svc.analyze("Total rockstar.", "review")
        assert result.ai_used is False

    def test_fallback_on_connection_error(self):
        """Even a network-level error should gracefully degrade."""
        failing = _make_failing_client(ConnectionError("Network unreachable"))
        svc = BiasDetectionService(ai_client=failing)
        result = svc.analyze("Some text.", "review")
        assert result is not None

    def test_fallback_on_json_parse_error(self):
        """Malformed Claude response should also degrade gracefully."""
        failing = _make_failing_client(ValueError("JSON decode error"))
        svc = BiasDetectionService(ai_client=failing)
        result = svc.analyze("Some text.", "review")
        assert result is not None

    def test_fallback_clean_text_still_clean(self):
        failing = _make_failing_client()
        svc = BiasDetectionService(ai_client=failing)
        result = svc.analyze("Clear communication and collaboration.", "review")
        assert result.flagged is False
        assert result.ai_used is False
