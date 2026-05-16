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


class TestPanelSizeInput:
    # ── valid sizes ──────────────────────────────────────────────────────────

    def test_panel_size_3_returns_3_interviewers(self):
        response = client.post(
            "/interviews/assign-panel",
            json={"interviewer_pool": DIVERSE_POOL, "panel_size": 3},
        )
        assert response.status_code == 200
        assert len(response.json()["interviewers"]) == 3

    def test_panel_size_4_returns_4_interviewers(self):
        response = client.post(
            "/interviews/assign-panel",
            json={"interviewer_pool": DIVERSE_POOL, "panel_size": 4},
        )
        assert response.status_code == 200
        assert len(response.json()["interviewers"]) == 4

    def test_omitting_panel_size_defaults_to_3(self):
        """Default must be the service minimum (3), not an arbitrary constant."""
        response = client.post(
            "/interviews/assign-panel",
            json={"interviewer_pool": DIVERSE_POOL},
        )
        assert response.status_code == 200
        assert len(response.json()["interviewers"]) == 3

    # ── boundary ─────────────────────────────────────────────────────────────

    def test_panel_size_at_minimum_succeeds(self):
        """3 is the lowest valid panel size — must not be rejected."""
        response = client.post(
            "/interviews/assign-panel",
            json={"interviewer_pool": DIVERSE_POOL, "panel_size": 3},
        )
        assert response.status_code == 200

    def test_panel_size_equal_to_pool_size_succeeds(self):
        """panel_size == len(pool) is valid — uses every available interviewer."""
        response = client.post(
            "/interviews/assign-panel",
            json={"interviewer_pool": DIVERSE_POOL, "panel_size": len(DIVERSE_POOL)},
        )
        assert response.status_code == 200
        assert len(response.json()["interviewers"]) == len(DIVERSE_POOL)

    def test_panel_size_exceeds_pool_returns_422(self):
        """Requesting more interviewers than are available must fail."""
        response = client.post(
            "/interviews/assign-panel",
            json={"interviewer_pool": DIVERSE_POOL, "panel_size": len(DIVERSE_POOL) + 1},
        )
        assert response.status_code == 422

    # ── edge cases ────────────────────────────────────────────────────────────

    def test_panel_size_below_minimum_returns_422(self):
        """panel_size=2 is below the service minimum of 3."""
        response = client.post(
            "/interviews/assign-panel",
            json={"interviewer_pool": DIVERSE_POOL, "panel_size": 2},
        )
        assert response.status_code == 422

    def test_panel_size_1_returns_422(self):
        """A single-person panel provides no diversity check."""
        response = client.post(
            "/interviews/assign-panel",
            json={"interviewer_pool": DIVERSE_POOL, "panel_size": 1},
        )
        assert response.status_code == 422
