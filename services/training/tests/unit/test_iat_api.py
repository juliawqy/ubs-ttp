"""
Unit tests for the IAT API router.
Run: pytest services/training/tests/unit/test_iat_api.py -v
"""
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def _start_session(employee_id="emp-1"):
    return client.post("/training/iat/sessions", json={"employee_id": employee_id}).json()


def _complete_session(session_id, employee_id="emp-1"):
    client.post(
        f"/training/iat/sessions/{session_id}/responses",
        json={"category": "cat", "selected_pole": "a", "response_time_ms": 600},
    )
    return client.post(f"/training/iat/sessions/{session_id}/complete").json()


class TestStartSession:
    def test_start_returns_201(self):
        response = client.post("/training/iat/sessions", json={"employee_id": "emp-1"})
        assert response.status_code == 201

    def test_start_returns_in_progress_status(self):
        session = _start_session()
        assert session["status"] == "in_progress"

    def test_start_preserves_employee_id(self):
        session = _start_session("emp-42")
        assert session["employee_id"] == "emp-42"

    def test_start_missing_employee_id_returns_422(self):
        response = client.post("/training/iat/sessions", json={"employee_id": ""})
        assert response.status_code == 422


class TestSubmitResponse:
    def test_submit_returns_200(self):
        session = _start_session()
        response = client.post(
            f"/training/iat/sessions/{session['id']}/responses",
            json={"category": "cat", "selected_pole": "a", "response_time_ms": 600},
        )
        assert response.status_code == 200

    def test_submit_increments_response_count(self):
        session = _start_session()
        client.post(
            f"/training/iat/sessions/{session['id']}/responses",
            json={"category": "cat", "selected_pole": "a", "response_time_ms": 600},
        )
        response = client.post(
            f"/training/iat/sessions/{session['id']}/responses",
            json={"category": "cat", "selected_pole": "b", "response_time_ms": 700},
        )
        assert response.json()["response_count"] == 2

    def test_submit_invalid_pole_returns_422(self):
        session = _start_session()
        response = client.post(
            f"/training/iat/sessions/{session['id']}/responses",
            json={"category": "cat", "selected_pole": "c", "response_time_ms": 600},
        )
        assert response.status_code == 422

    def test_submit_to_nonexistent_session_returns_404(self):
        response = client.post(
            "/training/iat/sessions/999999/responses",
            json={"category": "cat", "selected_pole": "a", "response_time_ms": 600},
        )
        assert response.status_code == 404

    def test_submit_after_completion_returns_422(self):
        session = _start_session()
        _complete_session(session["id"])
        response = client.post(
            f"/training/iat/sessions/{session['id']}/responses",
            json={"category": "cat", "selected_pole": "a", "response_time_ms": 600},
        )
        assert response.status_code == 422


class TestCompleteSession:
    def test_complete_returns_200(self):
        session = _start_session()
        client.post(
            f"/training/iat/sessions/{session['id']}/responses",
            json={"category": "cat", "selected_pole": "a", "response_time_ms": 600},
        )
        response = client.post(f"/training/iat/sessions/{session['id']}/complete")
        assert response.status_code == 200

    def test_complete_returns_category_scores(self):
        session = _start_session()
        result = _complete_session(session["id"])
        assert "cat" in result["category_scores"]

    def test_complete_with_no_responses_returns_422(self):
        session = _start_session()
        response = client.post(f"/training/iat/sessions/{session['id']}/complete")
        assert response.status_code == 422

    def test_complete_twice_returns_422(self):
        session = _start_session()
        _complete_session(session["id"])
        response = client.post(f"/training/iat/sessions/{session['id']}/complete")
        assert response.status_code == 422

    def test_complete_nonexistent_session_returns_404(self):
        response = client.post("/training/iat/sessions/999999/complete")
        assert response.status_code == 404


class TestGetResult:
    def test_owner_can_fetch_result(self):
        session = _start_session("emp-1")
        _complete_session(session["id"], "emp-1")
        response = client.get(
            f"/training/iat/sessions/{session['id']}/result", params={"employee_id": "emp-1"}
        )
        assert response.status_code == 200

    def test_other_employee_gets_403(self):
        session = _start_session("emp-1")
        _complete_session(session["id"], "emp-1")
        response = client.get(
            f"/training/iat/sessions/{session['id']}/result", params={"employee_id": "emp-2"}
        )
        assert response.status_code == 403

    def test_result_before_completion_returns_409(self):
        session = _start_session("emp-1")
        response = client.get(
            f"/training/iat/sessions/{session['id']}/result", params={"employee_id": "emp-1"}
        )
        assert response.status_code == 409

    def test_result_for_nonexistent_session_returns_404(self):
        response = client.get(
            "/training/iat/sessions/999999/result", params={"employee_id": "emp-1"}
        )
        assert response.status_code == 404
