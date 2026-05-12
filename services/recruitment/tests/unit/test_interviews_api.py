"""
Unit tests for the interviews / panel assignment API router.
Run: pytest services/recruitment/tests/unit/test_interviews_api.py -v
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

DIVERSE_POOL = [
    {"id": "i1", "name": "Alex Chen", "gender": "male", "department": "engineering"},
    {"id": "i2", "name": "Sara Patel", "gender": "female", "department": "product"},
    {"id": "i3", "name": "James Obi", "gender": "male", "department": "hr"},
    {"id": "i4", "name": "Mei Lin", "gender": "female", "department": "design"},
]

HOMOGENEOUS_POOL = [
    {"id": "i1", "name": "John Smith", "gender": "male", "department": "engineering"},
    {"id": "i2", "name": "Mike Jones", "gender": "male", "department": "engineering"},
    {"id": "i3", "name": "Tom Brown", "gender": "male", "department": "engineering"},
]


class TestPanelAssignment:
    def test_assign_diverse_panel_returns_200(self):
        response = client.post(
            "/interviews/assign-panel",
            json={"interviewer_pool": DIVERSE_POOL, "panel_size": 3},
        )
        assert response.status_code == 200

    def test_assignment_returns_approved_true_for_diverse_pool(self):
        response = client.post(
            "/interviews/assign-panel",
            json={"interviewer_pool": DIVERSE_POOL, "panel_size": 3},
        )
        assert response.json()["approved"] is True

    def test_assignment_returns_interviewer_list(self):
        response = client.post(
            "/interviews/assign-panel",
            json={"interviewer_pool": DIVERSE_POOL, "panel_size": 3},
        )
        assert "interviewers" in response.json()
        assert len(response.json()["interviewers"]) == 3

    def test_homogeneous_pool_returns_200_but_not_approved(self):
        """API returns 200 with approved=False and reason — does not hard reject."""
        response = client.post(
            "/interviews/assign-panel",
            json={"interviewer_pool": HOMOGENEOUS_POOL, "panel_size": 3},
        )
        assert response.status_code == 200
        assert response.json()["approved"] is False

    def test_rejected_panel_includes_reason(self):
        response = client.post(
            "/interviews/assign-panel",
            json={"interviewer_pool": HOMOGENEOUS_POOL, "panel_size": 3},
        )
        assert response.json()["rejection_reason"] is not None

    def test_pool_too_small_returns_422(self):
        response = client.post(
            "/interviews/assign-panel",
            json={"interviewer_pool": HOMOGENEOUS_POOL[:2], "panel_size": 3},
        )
        assert response.status_code == 422

    def test_empty_pool_returns_422(self):
        response = client.post(
            "/interviews/assign-panel",
            json={"interviewer_pool": [], "panel_size": 3},
        )
        assert response.status_code == 422

    def test_missing_pool_returns_422(self):
        response = client.post(
            "/interviews/assign-panel",
            json={"panel_size": 3},
        )
        assert response.status_code == 422
