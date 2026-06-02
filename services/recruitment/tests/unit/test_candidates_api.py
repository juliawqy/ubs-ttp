"""
Unit tests for the candidates API router.
Run: pytest services/recruitment/tests/unit/test_candidates_api.py -v
"""
import io
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestHealthCheck:
    def test_health_returns_ok(self):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"


class TestCandidateUpload:
    def test_upload_pdf_returns_200(self):
        fake_pdf = io.BytesIO(b"%PDF-1.4 fake pdf content with email test@example.com")
        response = client.post(
            "/candidates/upload",
            files={"file": ("cv.pdf", fake_pdf, "application/pdf")},
        )
        assert response.status_code == 200

    def test_upload_returns_redacted_text(self):
        fake_pdf = io.BytesIO(b"%PDF-1.4 contact: julia@example.com phone +65 9123 4567")
        response = client.post(
            "/candidates/upload",
            files={"file": ("cv.pdf", fake_pdf, "application/pdf")},
        )
        body = response.json()
        assert "redacted_text" in body
        assert "julia@example.com" not in body["redacted_text"]

    def test_upload_returns_candidate_id(self):
        fake_pdf = io.BytesIO(b"%PDF-1.4 some cv content")
        response = client.post(
            "/candidates/upload",
            files={"file": ("cv.pdf", fake_pdf, "application/pdf")},
        )
        assert "candidate_id" in response.json()

    def test_upload_with_no_file_returns_422(self):
        response = client.post("/candidates/upload")
        assert response.status_code == 422

    def test_upload_wrong_content_type_returns_400(self):
        response = client.post(
            "/candidates/upload",
            files={"file": ("cv.exe", io.BytesIO(b"binary"), "application/octet-stream")},
        )
        assert response.status_code == 400

    def test_upload_stores_pii_map_server_side(self):
        """PII map must never be returned to client — stays server side."""
        fake_pdf = io.BytesIO(b"%PDF-1.4 julia@example.com")
        response = client.post(
            "/candidates/upload",
            files={"file": ("cv.pdf", fake_pdf, "application/pdf")},
        )
        body = response.json()
        assert "pii_map" not in body


class TestCandidateList:
    def test_get_candidates_returns_200(self):
        response = client.get("/candidates")
        assert response.status_code == 200

    def test_get_candidates_returns_list(self):
        response = client.get("/candidates")
        assert isinstance(response.json(), list)


class TestCandidateAssessment:
    def test_assess_candidate_returns_200(self):
        payload = {
            "criteria": [
                {"name": "python", "weight": 0.6, "required": True},
                {"name": "sql", "weight": 0.4, "required": True},
            ],
            "scores": {"python": 8, "sql": 7},
        }
        response = client.post("/candidates/assess", json=payload)
        assert response.status_code == 200

    def test_assess_returns_total_score(self):
        payload = {
            "criteria": [
                {"name": "python", "weight": 0.6, "required": True},
                {"name": "sql", "weight": 0.4, "required": True},
            ],
            "scores": {"python": 10, "sql": 10},
        }
        response = client.post("/candidates/assess", json=payload)
        assert "total_score" in response.json()

    def test_assess_missing_required_skill_returns_422(self):
        payload = {
            "criteria": [
                {"name": "python", "weight": 1.0, "required": True},
            ],
            "scores": {},
        }
        response = client.post("/candidates/assess", json=payload)
        assert response.status_code == 422
