"""
Unit tests for the career mapping API router.
Run: pytest services/training/tests/unit/test_career_mapping_api.py -v
"""
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

VALID_ENTRY = {
    "employee_name": "Jane Doe",
    "current_role": "Software Engineer",
    "next_milestone": "Senior Software Engineer",
    "target_date": "2027-01-01",
}


class TestCreateEntry:
    def test_create_returns_201(self):
        response = client.post("/training/career-mapping", json=VALID_ENTRY)
        assert response.status_code == 201

    def test_create_returns_id(self):
        response = client.post("/training/career-mapping", json=VALID_ENTRY)
        assert "id" in response.json()

    def test_create_returns_recommended_skills(self):
        response = client.post("/training/career-mapping", json=VALID_ENTRY)
        assert "System Design" in response.json()["recommended_skills"]

    def test_missing_employee_name_returns_422(self):
        response = client.post(
            "/training/career-mapping", json={**VALID_ENTRY, "employee_name": ""}
        )
        assert response.status_code == 422


class TestListAndGet:
    def test_list_returns_200(self):
        response = client.get("/training/career-mapping")
        assert response.status_code == 200

    def test_list_returns_list(self):
        response = client.get("/training/career-mapping")
        assert isinstance(response.json(), list)

    def test_get_by_id_returns_200(self):
        created = client.post("/training/career-mapping", json=VALID_ENTRY).json()
        response = client.get(f"/training/career-mapping/{created['id']}")
        assert response.status_code == 200

    def test_get_nonexistent_returns_404(self):
        response = client.get("/training/career-mapping/999999")
        assert response.status_code == 404


class TestUpdateEntry:
    def _create(self):
        return client.post("/training/career-mapping", json=VALID_ENTRY).json()["id"]

    def test_update_returns_200(self):
        entry_id = self._create()
        updated = {**VALID_ENTRY, "next_milestone": "Staff Software Engineer"}
        response = client.put(f"/training/career-mapping/{entry_id}", json=updated)
        assert response.status_code == 200

    def test_update_changes_milestone(self):
        entry_id = self._create()
        updated = {**VALID_ENTRY, "next_milestone": "Staff Software Engineer"}
        response = client.put(f"/training/career-mapping/{entry_id}", json=updated)
        assert response.json()["next_milestone"] == "Staff Software Engineer"

    def test_update_preserves_id(self):
        entry_id = self._create()
        response = client.put(f"/training/career-mapping/{entry_id}", json=VALID_ENTRY)
        assert response.json()["id"] == entry_id

    def test_update_nonexistent_returns_404(self):
        response = client.put("/training/career-mapping/999999", json=VALID_ENTRY)
        assert response.status_code == 404

    def test_update_missing_employee_name_returns_422(self):
        entry_id = self._create()
        response = client.put(
            f"/training/career-mapping/{entry_id}", json={**VALID_ENTRY, "employee_name": ""}
        )
        assert response.status_code == 422


class TestDeleteEntry:
    def test_delete_returns_204(self):
        entry_id = client.post("/training/career-mapping", json=VALID_ENTRY).json()["id"]
        response = client.delete(f"/training/career-mapping/{entry_id}")
        assert response.status_code == 204

    def test_deleted_entry_returns_404_on_get(self):
        entry_id = client.post("/training/career-mapping", json=VALID_ENTRY).json()["id"]
        client.delete(f"/training/career-mapping/{entry_id}")
        response = client.get(f"/training/career-mapping/{entry_id}")
        assert response.status_code == 404

    def test_delete_nonexistent_returns_404(self):
        response = client.delete("/training/career-mapping/999999")
        assert response.status_code == 404
