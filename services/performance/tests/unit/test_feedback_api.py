"""
Unit tests for the feedback API router.
Run: pytest services/performance/tests/unit/test_feedback_api.py -v
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def _valid_payload(**overrides):
    payload = {
        "employee_id": "emp-fb-1",
        "rater_id": "rater-fb-1",
        "comments": "Great collaborator on cross-team projects.",
    }
    payload.update(overrides)
    return payload


# -- submit ---------------------------------------------------------------------

class TestSubmitFeedback:
    def test_submit_feedback_returns_201(self):
        response = client.post("/feedback", json=_valid_payload())
        assert response.status_code == 201

    def test_submit_feedback_preserves_employee_id(self):
        response = client.post("/feedback", json=_valid_payload())
        assert response.json()["employee_id"] == "emp-fb-1"

    def test_submit_feedback_preserves_comments(self):
        response = client.post("/feedback", json=_valid_payload())
        assert response.json()["comments"] == "Great collaborator on cross-team projects."

    def test_submit_feedback_empty_employee_id_returns_422(self):
        payload = _valid_payload(employee_id="")
        response = client.post("/feedback", json=payload)
        assert response.status_code == 422

    def test_submit_feedback_empty_rater_id_returns_422(self):
        payload = _valid_payload(rater_id="")
        response = client.post("/feedback", json=payload)
        assert response.status_code == 422

    def test_submit_feedback_empty_comments_returns_422(self):
        payload = _valid_payload(comments="")
        response = client.post("/feedback", json=payload)
        assert response.status_code == 422

    def test_submit_duplicate_feedback_returns_422(self):
        payload = _valid_payload(employee_id="emp-fb-dup", rater_id="rater-fb-dup")
        client.post("/feedback", json=payload)
        response = client.post("/feedback", json=payload)
        assert response.status_code == 422

    def test_submit_duplicate_feedback_error_mentions_already_submitted(self):
        payload = _valid_payload(employee_id="emp-fb-dup2", rater_id="rater-fb-dup2")
        client.post("/feedback", json=payload)
        response = client.post("/feedback", json=payload)
        assert "already submitted" in response.json()["detail"]


# -- aggregated view --------------------------------------------------------------

class TestGetAggregatedFeedback:
    def test_get_aggregated_returns_200(self):
        response = client.get("/feedback/emp-fb-agg")
        assert response.status_code == 200

    def test_get_aggregated_for_unknown_employee_is_empty(self):
        response = client.get("/feedback/emp-fb-nobody")
        body = response.json()
        assert body["count"] == 0
        assert body["comments"] == []

    def test_get_aggregated_includes_submitted_comments(self):
        client.post("/feedback", json=_valid_payload(employee_id="emp-fb-agg2", rater_id="rater-a", comments="Strong technical contributor."))
        client.post("/feedback", json=_valid_payload(employee_id="emp-fb-agg2", rater_id="rater-b", comments="Could improve on deadlines."))
        response = client.get("/feedback/emp-fb-agg2")
        body = response.json()
        assert body["count"] == 2
        assert set(body["comments"]) == {"Strong technical contributor.", "Could improve on deadlines."}

    def test_get_aggregated_never_exposes_rater_id(self):
        client.post("/feedback", json=_valid_payload(employee_id="emp-fb-agg3", rater_id="rater-secret", comments="Some feedback."))
        response = client.get("/feedback/emp-fb-agg3")
        body = response.json()
        assert "rater_id" not in body
        assert "rater-secret" not in str(body)

    def test_get_aggregated_employee_id_matches_path(self):
        client.post("/feedback", json=_valid_payload(employee_id="emp-fb-agg4", rater_id="rater-x"))
        response = client.get("/feedback/emp-fb-agg4")
        assert response.json()["employee_id"] == "emp-fb-agg4"
