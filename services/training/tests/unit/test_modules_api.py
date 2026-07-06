"""
Unit tests for the training modules API router.
Run: pytest services/training/tests/unit/test_modules_api.py -v
"""
from datetime import date, timedelta
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

VALID_MODULE = {
    "title": "Anti-Bias Fundamentals",
    "assigned_to": "Jane Doe",
    "due_date": str(date.today() + timedelta(days=30)),
    "description": "Intro module on recognising unconscious bias.",
}


class TestCreateModule:
    def test_create_returns_201(self):
        response = client.post("/training/modules", json=VALID_MODULE)
        assert response.status_code == 201

    def test_create_returns_id(self):
        response = client.post("/training/modules", json=VALID_MODULE)
        assert "id" in response.json()

    def test_create_status_is_not_started(self):
        response = client.post("/training/modules", json=VALID_MODULE)
        assert response.json()["status"] == "not_started"

    def test_create_completion_pct_is_zero(self):
        response = client.post("/training/modules", json=VALID_MODULE)
        assert response.json()["completion_pct"] == 0

    def test_missing_title_returns_422(self):
        response = client.post("/training/modules", json={**VALID_MODULE, "title": ""})
        assert response.status_code == 422

    def test_missing_assigned_to_returns_422(self):
        response = client.post("/training/modules", json={**VALID_MODULE, "assigned_to": ""})
        assert response.status_code == 422


class TestListAndGet:
    def test_list_returns_200(self):
        response = client.get("/training/modules")
        assert response.status_code == 200

    def test_list_returns_list(self):
        response = client.get("/training/modules")
        assert isinstance(response.json(), list)

    def test_get_by_id_returns_200(self):
        created = client.post("/training/modules", json=VALID_MODULE).json()
        response = client.get(f"/training/modules/{created['id']}")
        assert response.status_code == 200

    def test_get_nonexistent_returns_404(self):
        response = client.get("/training/modules/999999")
        assert response.status_code == 404


class TestUpdateModule:
    def _create(self):
        return client.post("/training/modules", json=VALID_MODULE).json()["id"]

    def test_update_returns_200(self):
        module_id = self._create()
        updated = {**VALID_MODULE, "title": "Advanced Bias Mitigation"}
        response = client.put(f"/training/modules/{module_id}", json=updated)
        assert response.status_code == 200

    def test_update_changes_title(self):
        module_id = self._create()
        updated = {**VALID_MODULE, "title": "Advanced Bias Mitigation"}
        response = client.put(f"/training/modules/{module_id}", json=updated)
        assert response.json()["title"] == "Advanced Bias Mitigation"

    def test_update_preserves_progress(self):
        module_id = self._create()
        client.patch(f"/training/modules/{module_id}/progress", json={"completion_pct": 60})
        response = client.put(f"/training/modules/{module_id}", json=VALID_MODULE)
        assert response.json()["completion_pct"] == 60
        assert response.json()["status"] == "in_progress"

    def test_update_nonexistent_returns_404(self):
        response = client.put("/training/modules/999999", json=VALID_MODULE)
        assert response.status_code == 404

    def test_update_missing_title_returns_422(self):
        module_id = self._create()
        response = client.put(f"/training/modules/{module_id}", json={**VALID_MODULE, "title": ""})
        assert response.status_code == 422


class TestDeleteModule:
    def test_delete_returns_204(self):
        module_id = client.post("/training/modules", json=VALID_MODULE).json()["id"]
        response = client.delete(f"/training/modules/{module_id}")
        assert response.status_code == 204

    def test_deleted_module_returns_404_on_get(self):
        module_id = client.post("/training/modules", json=VALID_MODULE).json()["id"]
        client.delete(f"/training/modules/{module_id}")
        response = client.get(f"/training/modules/{module_id}")
        assert response.status_code == 404

    def test_delete_nonexistent_returns_404(self):
        response = client.delete("/training/modules/999999")
        assert response.status_code == 404


class TestProgress:
    def _create(self):
        return client.post("/training/modules", json=VALID_MODULE).json()["id"]

    def test_update_progress_returns_200(self):
        module_id = self._create()
        response = client.patch(f"/training/modules/{module_id}/progress", json={"completion_pct": 50})
        assert response.status_code == 200

    def test_progress_above_100_returns_422(self):
        module_id = self._create()
        response = client.patch(f"/training/modules/{module_id}/progress", json={"completion_pct": 150})
        assert response.status_code == 422

    def test_full_completion_sets_status_completed(self):
        module_id = self._create()
        response = client.patch(f"/training/modules/{module_id}/progress", json={"completion_pct": 100})
        assert response.json()["status"] == "completed"

    def test_progress_nonexistent_returns_404(self):
        response = client.patch("/training/modules/999999/progress", json={"completion_pct": 50})
        assert response.status_code == 404


class TestRemind:
    def test_overdue_module_can_be_reminded(self):
        overdue = {**VALID_MODULE, "due_date": str(date.today() - timedelta(days=1))}
        module_id = client.post("/training/modules", json=overdue).json()["id"]
        response = client.post(f"/training/modules/{module_id}/remind")
        assert response.status_code == 200

    def test_remind_increments_reminder_count(self):
        overdue = {**VALID_MODULE, "due_date": str(date.today() - timedelta(days=1))}
        module_id = client.post("/training/modules", json=overdue).json()["id"]
        response = client.post(f"/training/modules/{module_id}/remind")
        assert response.json()["reminder_count"] == 1

    def test_not_due_module_returns_409(self):
        not_due = {**VALID_MODULE, "due_date": str(date.today() + timedelta(days=60))}
        module_id = client.post("/training/modules", json=not_due).json()["id"]
        response = client.post(f"/training/modules/{module_id}/remind")
        assert response.status_code == 409

    def test_remind_nonexistent_returns_404(self):
        response = client.post("/training/modules/999999/remind")
        assert response.status_code == 404

    def test_completed_module_cannot_be_reminded(self):
        module_id = client.post("/training/modules", json=VALID_MODULE).json()["id"]
        client.patch(f"/training/modules/{module_id}/progress", json={"completion_pct": 100})
        response = client.post(f"/training/modules/{module_id}/remind")
        assert response.status_code == 409


class TestDueDateValidation:
    """due_date must be today or in the future."""

    def test_past_due_date_returns_422(self):
        payload = {**VALID_MODULE, "due_date": str(date.today() - timedelta(days=1))}
        response = client.post("/training/modules", json=payload)
        assert response.status_code == 422

    def test_far_past_due_date_returns_422(self):
        payload = {**VALID_MODULE, "due_date": "2020-01-01"}
        response = client.post("/training/modules", json=payload)
        assert response.status_code == 422

    def test_today_as_due_date_is_accepted(self):
        payload = {**VALID_MODULE, "due_date": str(date.today())}
        response = client.post("/training/modules", json=payload)
        assert response.status_code == 201

    def test_future_due_date_is_accepted(self):
        payload = {**VALID_MODULE, "due_date": str(date.today() + timedelta(days=1))}
        response = client.post("/training/modules", json=payload)
        assert response.status_code == 201

    def test_past_due_date_error_is_descriptive(self):
        payload = {**VALID_MODULE, "due_date": str(date.today() - timedelta(days=1))}
        response = client.post("/training/modules", json=payload)
        detail = str(response.json())
        assert "due_date" in detail or "future" in detail or "today" in detail
