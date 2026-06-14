"""
Unit tests for the candidates API router.
Run: pytest services/recruitment/tests/unit/test_candidates_api.py -v
"""
import io
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


# -- helpers ------------------------------------------------------------------

def _upload_candidate(content: bytes = b"%PDF-1.4 candidate cv content") -> int:
    """Upload a candidate and return the assigned candidate_id."""
    response = client.post(
        "/candidates/upload",
        files={"file": ("cv.pdf", io.BytesIO(content), "application/pdf")},
    )
    assert response.status_code == 200
    return response.json()["candidate_id"]


# -- health -------------------------------------------------------------------

class TestHealthCheck:
    def test_health_returns_ok(self):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"


# -- upload -------------------------------------------------------------------

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
        """PII map must never be returned to client."""
        fake_pdf = io.BytesIO(b"%PDF-1.4 julia@example.com")
        response = client.post(
            "/candidates/upload",
            files={"file": ("cv.pdf", fake_pdf, "application/pdf")},
        )
        body = response.json()
        assert "pii_map" not in body


# -- list ---------------------------------------------------------------------

class TestCandidateList:
    def test_get_candidates_returns_200(self):
        response = client.get("/candidates")
        assert response.status_code == 200

    def test_get_candidates_returns_list(self):
        response = client.get("/candidates")
        assert isinstance(response.json(), list)

    def test_listed_candidates_have_status(self):
        _upload_candidate()
        response = client.get("/candidates")
        items = response.json()
        assert all("status" in c for c in items)


# -- get by id ----------------------------------------------------------------

class TestCandidateGet:
    def test_get_existing_candidate_returns_200(self):
        cid = _upload_candidate()
        response = client.get(f"/candidates/{cid}")
        assert response.status_code == 200

    def test_get_returns_candidate_id(self):
        cid = _upload_candidate()
        response = client.get(f"/candidates/{cid}")
        assert response.json()["candidate_id"] == cid

    def test_get_returns_redacted_text(self):
        cid = _upload_candidate()
        response = client.get(f"/candidates/{cid}")
        assert "redacted_text" in response.json()

    def test_get_returns_status(self):
        cid = _upload_candidate()
        response = client.get(f"/candidates/{cid}")
        assert response.json()["status"] == "pending"

    def test_get_does_not_return_pii_map(self):
        cid = _upload_candidate()
        response = client.get(f"/candidates/{cid}")
        assert "_pii_map" not in response.json()
        assert "pii_map" not in response.json()

    def test_get_unknown_candidate_returns_404(self):
        response = client.get("/candidates/99999")
        assert response.status_code == 404


# -- assess -------------------------------------------------------------------

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
            "criteria": [{"name": "python", "weight": 1.0, "required": True}],
            "scores": {},
        }
        response = client.post("/candidates/assess", json=payload)
        assert response.status_code == 422


# -- decide -------------------------------------------------------------------

class TestHireDecision:
    def test_decide_hired_returns_200(self):
        cid = _upload_candidate()
        response = client.post(
            f"/candidates/{cid}/decide",
            json={"decision": "hired", "justification": "Strong technical skills."},
        )
        assert response.status_code == 200

    def test_decide_rejected_returns_200(self):
        cid = _upload_candidate()
        response = client.post(
            f"/candidates/{cid}/decide",
            json={"decision": "rejected", "justification": "Does not meet SQL requirements."},
        )
        assert response.status_code == 200

    def test_decide_returns_candidate_id(self):
        cid = _upload_candidate()
        response = client.post(
            f"/candidates/{cid}/decide",
            json={"decision": "hired", "justification": "Excellent communicator."},
        )
        assert response.json()["candidate_id"] == cid

    def test_decide_returns_decision(self):
        cid = _upload_candidate()
        response = client.post(
            f"/candidates/{cid}/decide",
            json={"decision": "rejected", "justification": "Lacks required experience."},
        )
        assert response.json()["decision"] == "rejected"

    def test_decide_returns_bias_check(self):
        cid = _upload_candidate()
        response = client.post(
            f"/candidates/{cid}/decide",
            json={"decision": "hired", "justification": "Solid performer."},
        )
        body = response.json()
        assert "bias_check" in body
        assert "flagged" in body["bias_check"]

    def test_decide_clean_justification_not_flagged(self):
        cid = _upload_candidate()
        response = client.post(
            f"/candidates/{cid}/decide",
            json={"decision": "hired", "justification": "Demonstrated strong Python and SQL skills."},
        )
        assert response.json()["bias_check"]["flagged"] is False

    def test_decide_biased_justification_is_flagged(self):
        cid = _upload_candidate()
        response = client.post(
            f"/candidates/{cid}/decide",
            json={"decision": "rejected", "justification": "Not enough of a rockstar for this team."},
        )
        assert response.json()["bias_check"]["flagged"] is True

    def test_decide_flagged_response_includes_phrases(self):
        cid = _upload_candidate()
        response = client.post(
            f"/candidates/{cid}/decide",
            json={"decision": "rejected", "justification": "Does not seem like a culture fit."},
        )
        body = response.json()
        assert len(body["bias_check"]["flagged_phrases"]) > 0
        phrase_obj = body["bias_check"]["flagged_phrases"][0]
        assert "phrase" in phrase_obj
        assert "suggestion" in phrase_obj

    def test_decide_unknown_candidate_returns_404(self):
        response = client.post(
            "/candidates/99999/decide",
            json={"decision": "hired", "justification": "Great candidate."},
        )
        assert response.status_code == 404

    def test_decide_invalid_decision_returns_422(self):
        cid = _upload_candidate()
        response = client.post(
            f"/candidates/{cid}/decide",
            json={"decision": "maybe", "justification": "Not sure."},
        )
        assert response.status_code == 422

    def test_decide_empty_justification_returns_422(self):
        cid = _upload_candidate()
        response = client.post(
            f"/candidates/{cid}/decide",
            json={"decision": "hired", "justification": ""},
        )
        assert response.status_code == 422

    def test_candidate_status_updates_after_decision(self):
        cid = _upload_candidate()
        client.post(
            f"/candidates/{cid}/decide",
            json={"decision": "hired", "justification": "Strong all-round candidate."},
        )
        response = client.get(f"/candidates/{cid}")
        assert response.json()["status"] == "hired"

    def test_decision_stored_on_candidate(self):
        cid = _upload_candidate()
        client.post(
            f"/candidates/{cid}/decide",
            json={"decision": "rejected", "justification": "Missing required Python experience."},
        )
        response = client.get(f"/candidates/{cid}")
        decision = response.json()["decision"]
        assert decision is not None
        assert decision["decision"] == "rejected"
