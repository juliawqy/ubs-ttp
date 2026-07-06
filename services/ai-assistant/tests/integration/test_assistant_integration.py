"""
Integration tests for POST /assistant/analyze (TTP-26).

These tests exercise the full HTTP stack — router schema validation,
dependency wiring, and service logic — by sending real HTTP requests via
TestClient with an AI client injected through FastAPI dependency_overrides.

Contrast with tests/unit/test_bias_detection_service.py, which tests the
service class in isolation.  Here we verify that the router, serialisation,
and service all cooperate correctly end-to-end.
"""
import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from app.main import app
from app.routers.assistant import get_service
from app.services.bias_classifier import BiasDetectionService
from app.models import BiasCategory


# ── mock helpers ──────────────────────────────────────────────────────────────

def _make_mock_service(response: dict) -> BiasDetectionService:
    mock_client = MagicMock()
    mock_client.analyze_bias.return_value = response
    return BiasDetectionService(ai_client=mock_client)


def _make_failing_service(exc: Exception | None = None) -> BiasDetectionService:
    mock_client = MagicMock()
    mock_client.analyze_bias.side_effect = exc or RuntimeError("Claude API unavailable")
    return BiasDetectionService(ai_client=mock_client)


MOCK_FLAGGED = {
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

MOCK_CLEAN = {
    "flagged": False,
    "phrases": [],
    "overall_suggestion": None,
}


@pytest.fixture(autouse=True)
def clear_overrides():
    """Ensure dependency_overrides are cleared after each test."""
    yield
    app.dependency_overrides.clear()


# ── HTTP-level: flagged response ───────────────────────────────────────────────

class TestFlaggedResponseHTTP:
    """Mocked AI returns a flagged result — verify the full HTTP response shape."""

    def _client(self) -> TestClient:
        app.dependency_overrides[get_service] = lambda: _make_mock_service(MOCK_FLAGGED)
        return TestClient(app)

    def test_returns_200(self):
        res = self._client().post("/assistant/analyze", json={"text": "We need a ninja."})
        assert res.status_code == 200

    def test_flagged_is_true(self):
        res = self._client().post("/assistant/analyze", json={"text": "We need a ninja."})
        assert res.json()["flagged"] is True

    def test_phrase_count_matches_mock(self):
        res = self._client().post("/assistant/analyze", json={"text": "We need a ninja."})
        assert len(res.json()["flagged_phrases"]) == 2

    def test_phrase_text_is_forwarded(self):
        res = self._client().post("/assistant/analyze", json={"text": "We need a ninja."})
        phrases = [p["phrase"] for p in res.json()["flagged_phrases"]]
        assert "ninja" in phrases
        assert "young and dynamic" in phrases

    def test_phrase_category_is_serialised(self):
        res = self._client().post("/assistant/analyze", json={"text": "We need a ninja."})
        ninja = next(p for p in res.json()["flagged_phrases"] if p["phrase"] == "ninja")
        assert ninja["category"] == "gender"

    def test_phrase_severity_is_serialised(self):
        res = self._client().post("/assistant/analyze", json={"text": "We need a ninja."})
        ninja = next(p for p in res.json()["flagged_phrases"] if p["phrase"] == "ninja")
        assert ninja["severity"] == 2

    def test_overall_suggestion_is_forwarded(self):
        res = self._client().post("/assistant/analyze", json={"text": "We need a ninja."})
        assert res.json()["overall_suggestion"] == "Use inclusive, skills-focused language throughout."

    def test_ai_used_is_true(self):
        res = self._client().post("/assistant/analyze", json={"text": "We need a ninja."})
        assert res.json()["ai_used"] is True


# ── HTTP-level: clean response ─────────────────────────────────────────────────

class TestCleanResponseHTTP:
    def _client(self) -> TestClient:
        app.dependency_overrides[get_service] = lambda: _make_mock_service(MOCK_CLEAN)
        return TestClient(app)

    def test_returns_200(self):
        res = self._client().post("/assistant/analyze", json={"text": "Strong communicator."})
        assert res.status_code == 200

    def test_flagged_is_false(self):
        res = self._client().post("/assistant/analyze", json={"text": "Strong communicator."})
        assert res.json()["flagged"] is False

    def test_flagged_phrases_is_empty(self):
        res = self._client().post("/assistant/analyze", json={"text": "Strong communicator."})
        assert res.json()["flagged_phrases"] == []


# ── HTTP-level: input validation ───────────────────────────────────────────────

class TestInputValidationHTTP:
    def _client(self) -> TestClient:
        app.dependency_overrides[get_service] = lambda: _make_mock_service(MOCK_CLEAN)
        return TestClient(app)

    def test_blank_text_returns_422(self):
        res = self._client().post("/assistant/analyze", json={"text": "   "})
        assert res.status_code == 422

    def test_missing_text_field_returns_422(self):
        res = self._client().post("/assistant/analyze", json={})
        assert res.status_code == 422

    def test_context_forwarded_to_ai_client(self):
        """Verify context flows through the full HTTP → service → AI client path."""
        mock_client = MagicMock()
        mock_client.analyze_bias.return_value = MOCK_CLEAN
        svc = BiasDetectionService(ai_client=mock_client)
        app.dependency_overrides[get_service] = lambda: svc
        client = TestClient(app)
        client.post("/assistant/analyze", json={"text": "Some text.", "context": "job_posting"})
        mock_client.analyze_bias.assert_called_once_with("Some text.", "job_posting")


# ── HTTP-level: fallback on AI failure ────────────────────────────────────────

class TestFallbackBehaviourHTTP:
    """AI failures must degrade gracefully — still return 200 via rule-based fallback."""

    def test_api_failure_returns_200(self):
        app.dependency_overrides[get_service] = lambda: _make_failing_service()
        res = TestClient(app).post("/assistant/analyze", json={"text": "Total rockstar."})
        assert res.status_code == 200

    def test_api_failure_still_catches_rule_based_flags(self):
        app.dependency_overrides[get_service] = lambda: _make_failing_service()
        res = TestClient(app).post("/assistant/analyze", json={"text": "We need a rockstar ninja."})
        assert res.json()["flagged"] is True

    def test_api_failure_sets_ai_used_false(self):
        app.dependency_overrides[get_service] = lambda: _make_failing_service()
        res = TestClient(app).post("/assistant/analyze", json={"text": "Total rockstar."})
        assert res.json()["ai_used"] is False

    def test_connection_error_degrades_gracefully(self):
        app.dependency_overrides[get_service] = lambda: _make_failing_service(
            ConnectionError("Network unreachable")
        )
        res = TestClient(app).post("/assistant/analyze", json={"text": "Some text."})
        assert res.status_code == 200

    def test_json_parse_error_degrades_gracefully(self):
        app.dependency_overrides[get_service] = lambda: _make_failing_service(
            ValueError("JSON decode error")
        )
        res = TestClient(app).post("/assistant/analyze", json={"text": "Some text."})
        assert res.status_code == 200
