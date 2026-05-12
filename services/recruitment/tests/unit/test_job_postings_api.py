"""
Unit tests for the job postings API router.
Run: pytest services/recruitment/tests/unit/test_job_postings_api.py -v
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

CLEAN_POSTING = {
    "title": "Senior Python Engineer",
    "description": "We are looking for an experienced Python engineer to build scalable APIs.",
    "requirements": ["Python", "SQL", "REST APIs"],
    "department": "Engineering",
}

BIASED_POSTING = {
    "title": "Rockstar Python Ninja",
    "description": "We need a rockstar ninja who is a great culture fit and a digital native.",
    "requirements": ["Python"],
    "department": "Engineering",
}


class TestCreateJobPosting:
    def test_create_clean_posting_returns_201(self):
        response = client.post("/job-postings", json=CLEAN_POSTING)
        assert response.status_code == 201

    def test_create_returns_posting_id(self):
        response = client.post("/job-postings", json=CLEAN_POSTING)
        assert "id" in response.json()

    def test_create_returns_bias_check_result(self):
        """Every posting creation must include a bias check result."""
        response = client.post("/job-postings", json=CLEAN_POSTING)
        assert "bias_check" in response.json()

    def test_biased_posting_still_saves_but_flags_warning(self):
        """Biased postings are saved but returned with warnings — manager decides."""
        response = client.post("/job-postings", json=BIASED_POSTING)
        assert response.status_code == 201
        body = response.json()
        assert body["bias_check"]["flagged"] is True

    def test_clean_posting_has_no_bias_flags(self):
        response = client.post("/job-postings", json=CLEAN_POSTING)
        body = response.json()
        assert body["bias_check"]["flagged"] is False

    def test_biased_posting_includes_flagged_phrases(self):
        response = client.post("/job-postings", json=BIASED_POSTING)
        flagged_phrases = response.json()["bias_check"]["flagged_phrases"]
        assert len(flagged_phrases) > 0

    def test_missing_title_returns_422(self):
        response = client.post("/job-postings", json={"description": "No title here"})
        assert response.status_code == 422

    def test_missing_description_returns_422(self):
        response = client.post("/job-postings", json={"title": "Engineer"})
        assert response.status_code == 422


class TestGetJobPostings:
    def test_get_all_returns_200(self):
        response = client.get("/job-postings")
        assert response.status_code == 200

    def test_get_all_returns_list(self):
        response = client.get("/job-postings")
        assert isinstance(response.json(), list)

    def test_get_by_id_returns_200(self):
        # Create first, then retrieve
        create_response = client.post("/job-postings", json=CLEAN_POSTING)
        posting_id = create_response.json()["id"]
        response = client.get(f"/job-postings/{posting_id}")
        assert response.status_code == 200

    def test_get_nonexistent_returns_404(self):
        response = client.get("/job-postings/nonexistent-id")
        assert response.status_code == 404
