"""
Unit tests for POST /assistant/analyze (TTP-24).
Written before implementation — TDD.
Run: pytest services/ai-assistant/tests/unit/test_assistant_api.py -v
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.routers.assistant import get_service
from app.services.bias_classifier import BiasDetectionService

client = TestClient(app)


def _valid_payload(**overrides):
    payload = {"text": "We need a rockstar engineer who is a digital native."}
    payload.update(overrides)
    return payload


# ── health ────────────────────────────────────────────────────────────────────

class TestHealthCheck:
    def test_health_returns_ok(self):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"


# ── POST /assistant/analyze ───────────────────────────────────────────────────

class TestAnalyzeEndpoint:
    def test_analyze_returns_200(self):
        response = client.post("/assistant/analyze", json=_valid_payload())
        assert response.status_code == 200

    def test_analyze_biased_text_flagged(self):
        response = client.post("/assistant/analyze", json=_valid_payload())
        assert response.json()["flagged"] is True

    def test_analyze_clean_text_not_flagged(self):
        response = client.post(
            "/assistant/analyze",
            json=_valid_payload(text="Demonstrated strong communication and collaboration."),
        )
        assert response.json()["flagged"] is False

    def test_analyze_response_includes_flagged_phrases(self):
        response = client.post("/assistant/analyze", json=_valid_payload())
        body = response.json()
        assert "flagged_phrases" in body
        assert isinstance(body["flagged_phrases"], list)

    def test_analyze_each_phrase_has_phrase_field(self):
        response = client.post("/assistant/analyze", json=_valid_payload())
        for phrase in response.json()["flagged_phrases"]:
            assert "phrase" in phrase

    def test_analyze_each_phrase_has_reason(self):
        response = client.post("/assistant/analyze", json=_valid_payload())
        for phrase in response.json()["flagged_phrases"]:
            assert "reason" in phrase

    def test_analyze_each_phrase_has_suggestion(self):
        response = client.post("/assistant/analyze", json=_valid_payload())
        for phrase in response.json()["flagged_phrases"]:
            assert "suggestion" in phrase

    def test_analyze_each_phrase_has_category(self):
        response = client.post("/assistant/analyze", json=_valid_payload())
        for phrase in response.json()["flagged_phrases"]:
            assert "category" in phrase

    def test_analyze_each_phrase_has_severity(self):
        response = client.post("/assistant/analyze", json=_valid_payload())
        for phrase in response.json()["flagged_phrases"]:
            assert "severity" in phrase
            assert isinstance(phrase["severity"], int)
            assert 1 <= phrase["severity"] <= 3

    def test_analyze_response_includes_ai_used(self):
        response = client.post("/assistant/analyze", json=_valid_payload())
        assert "ai_used" in response.json()

    def test_analyze_response_includes_overall_suggestion(self):
        response = client.post("/assistant/analyze", json=_valid_payload())
        assert "overall_suggestion" in response.json()

    def test_analyze_context_field_is_optional(self):
        # No context field — should default and not 422
        response = client.post("/assistant/analyze", json={"text": "Some text."})
        assert response.status_code == 200

    def test_analyze_with_explicit_context(self):
        response = client.post(
            "/assistant/analyze",
            json={"text": "We need a ninja developer.", "context": "job_posting"},
        )
        assert response.status_code == 200

    def test_analyze_missing_text_returns_422(self):
        response = client.post("/assistant/analyze", json={})
        assert response.status_code == 422

    def test_analyze_empty_text_returns_422(self):
        response = client.post("/assistant/analyze", json={"text": ""})
        assert response.status_code == 422

    def test_analyze_whitespace_text_returns_422(self):
        response = client.post("/assistant/analyze", json={"text": "   "})
        assert response.status_code == 422

    def test_analyze_rockstar_flagged_as_gender(self):
        response = client.post(
            "/assistant/analyze",
            json={"text": "Total rockstar on the team.", "context": "review"},
        )
        body = response.json()
        gender_phrases = [
            p for p in body["flagged_phrases"]
            if p["category"] == "gender"
        ]
        assert len(gender_phrases) > 0

    def test_analyze_digital_native_flagged_as_age(self):
        response = client.post(
            "/assistant/analyze",
            json={"text": "Must be a digital native.", "context": "job_posting"},
        )
        body = response.json()
        age_phrases = [
            p for p in body["flagged_phrases"]
            if p["category"] == "age"
        ]
        assert len(age_phrases) > 0


class TestGetServiceDependency:
    """Covers the get_service() factory — bypassed in other tests via dependency_overrides."""

    def test_get_service_returns_bias_detection_service(self):
        """get_service() must return a BiasDetectionService even with no API key set."""
        import os
        os.environ.pop("ANTHROPIC_API_KEY", None)
        svc = get_service()
        assert isinstance(svc, BiasDetectionService)

    def test_get_service_with_empty_key_still_returns_service(self):
        """An empty key must not raise — ClaudeClient is instantiated with empty string."""
        import os
        os.environ["ANTHROPIC_API_KEY"] = ""
        svc = get_service()
        assert isinstance(svc, BiasDetectionService)
        os.environ.pop("ANTHROPIC_API_KEY", None)
