"""
Unit tests for the job postings API router.
Run: pytest services/recruitment/tests/unit/test_job_postings_api.py -v
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

MANAGER = {
    "id": "mgr-001",
    "name": "Julia Wong",
    "department": "Engineering",
    "email": "julia.wong@ubs.com",
}

CLEAN_POSTING = {
    "title": "Senior Python Engineer",
    "description": "We are looking for an experienced Python engineer to build scalable APIs.",
    "requirements": ["Python", "SQL", "REST APIs"],
    "department": "Engineering",
    "manager": MANAGER,
}

BIASED_POSTING = {
    "title": "Rockstar Python Ninja",
    "description": "We need a rockstar ninja who is a great culture fit and a digital native.",
    "requirements": ["Python"],
    "department": "Engineering",
    "manager": MANAGER,
}


class TestCreateJobPosting:
    def test_create_clean_posting_returns_201(self):
        response = client.post("/job-postings", json=CLEAN_POSTING)
        assert response.status_code == 201

    def test_create_returns_posting_id(self):
        response = client.post("/job-postings", json=CLEAN_POSTING)
        assert "id" in response.json()

    def test_create_returns_bias_check_result(self):
        response = client.post("/job-postings", json=CLEAN_POSTING)
        assert "bias_check" in response.json()

    def test_biased_posting_still_saves_but_flags_warning(self):
        """Biased postings are saved but returned with warnings — manager decides."""
        response = client.post("/job-postings", json=BIASED_POSTING)
        assert response.status_code == 201
        assert response.json()["bias_check"]["flagged"] is True

    def test_clean_posting_has_no_bias_flags(self):
        response = client.post("/job-postings", json=CLEAN_POSTING)
        assert response.json()["bias_check"]["flagged"] is False

    def test_biased_posting_includes_flagged_phrases(self):
        response = client.post("/job-postings", json=BIASED_POSTING)
        assert len(response.json()["bias_check"]["flagged_phrases"]) > 0

    def test_status_is_pending(self):
        response = client.post("/job-postings", json=CLEAN_POSTING)
        assert response.json()["status"] == "pending"

    def test_manager_details_returned(self):
        response = client.post("/job-postings", json=CLEAN_POSTING)
        mgr = response.json()["manager"]
        assert mgr["id"] == MANAGER["id"]
        assert mgr["name"] == MANAGER["name"]
        assert mgr["department"] == MANAGER["department"]
        assert mgr["email"] == MANAGER["email"]

    def test_missing_title_returns_422(self):
        response = client.post("/job-postings", json={**CLEAN_POSTING, "title": ""})
        assert response.status_code == 422

    def test_missing_description_returns_422(self):
        response = client.post("/job-postings", json={**CLEAN_POSTING, "description": ""})
        assert response.status_code == 422

    def test_missing_manager_returns_422(self):
        payload = {k: v for k, v in CLEAN_POSTING.items() if k != "manager"}
        response = client.post("/job-postings", json=payload)
        assert response.status_code == 422

    def test_invalid_manager_email_returns_422(self):
        bad_manager = {**MANAGER, "email": "not-an-email"}
        response = client.post("/job-postings", json={**CLEAN_POSTING, "manager": bad_manager})
        assert response.status_code == 422


class TestGetJobPostings:
    def test_get_all_returns_200(self):
        response = client.get("/job-postings")
        assert response.status_code == 200

    def test_get_all_returns_list(self):
        response = client.get("/job-postings")
        assert isinstance(response.json(), list)

    def test_get_by_id_returns_200(self):
        create_response = client.post("/job-postings", json=CLEAN_POSTING)
        posting_id = create_response.json()["id"]
        response = client.get(f"/job-postings/{posting_id}")
        assert response.status_code == 200

    def test_get_nonexistent_returns_404(self):
        response = client.get("/job-postings/nonexistent-id")
        assert response.status_code == 404


class TestUpdateJobPosting:
    def _create(self, payload=None):
        response = client.post("/job-postings", json=payload or CLEAN_POSTING)
        return response.json()["id"]

    def test_update_returns_200(self):
        pid = self._create()
        updated = {**CLEAN_POSTING, "title": "Staff Python Engineer"}
        response = client.put(f"/job-postings/{pid}", json=updated)
        assert response.status_code == 200

    def test_update_changes_fields(self):
        pid = self._create()
        updated = {**CLEAN_POSTING, "title": "Staff Python Engineer", "department": "Platform"}
        response = client.put(f"/job-postings/{pid}", json=updated)
        body = response.json()
        assert body["title"] == "Staff Python Engineer"
        assert body["department"] == "Platform"

    def test_update_preserves_id(self):
        pid = self._create()
        response = client.put(f"/job-postings/{pid}", json=CLEAN_POSTING)
        assert response.json()["id"] == pid

    def test_update_preserves_existing_status(self):
        """Editing a posting must not reset its workflow status back to pending."""
        pid = self._create()
        original_status = client.get(f"/job-postings/{pid}").json()["status"]
        response = client.put(f"/job-postings/{pid}", json=CLEAN_POSTING)
        assert response.json()["status"] == original_status

    def test_update_runs_bias_check_on_new_content(self):
        pid = self._create()
        response = client.put(f"/job-postings/{pid}", json=BIASED_POSTING)
        assert response.json()["bias_check"]["flagged"] is True

    def test_update_persists_via_get(self):
        pid = self._create()
        updated = {**CLEAN_POSTING, "title": "Staff Python Engineer"}
        client.put(f"/job-postings/{pid}", json=updated)
        response = client.get(f"/job-postings/{pid}")
        assert response.json()["title"] == "Staff Python Engineer"

    def test_update_nonexistent_returns_404(self):
        response = client.put("/job-postings/999999", json=CLEAN_POSTING)
        assert response.status_code == 404

    def test_update_missing_manager_returns_422(self):
        pid = self._create()
        payload = {k: v for k, v in CLEAN_POSTING.items() if k != "manager"}
        response = client.put(f"/job-postings/{pid}", json=payload)
        assert response.status_code == 422
