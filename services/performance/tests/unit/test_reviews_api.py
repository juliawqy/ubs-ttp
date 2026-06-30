"""
Unit tests for the reviews API router.
Run: pytest services/performance/tests/unit/test_reviews_api.py -v
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def _valid_payload(**overrides):
    payload = {
        "employee_id": "emp-1",
        "reviewer_id": "mgr-1",
        "criteria": [
            {"criterion": "technical_skill", "score": 5, "comments": "Strong technical depth."},
            {"criterion": "communication", "score": 4, "comments": "Clear and concise."},
        ],
    }
    payload.update(overrides)
    return payload


# -- health -------------------------------------------------------------------

class TestHealthCheck:
    def test_health_returns_ok(self):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"


# -- create -------------------------------------------------------------------

class TestCreateReview:
    def test_create_review_returns_201(self):
        response = client.post("/reviews", json=_valid_payload())
        assert response.status_code == 201

    def test_create_review_returns_id(self):
        response = client.post("/reviews", json=_valid_payload())
        assert "id" in response.json()

    def test_create_review_preserves_employee_id(self):
        response = client.post("/reviews", json=_valid_payload())
        assert response.json()["employee_id"] == "emp-1"

    def test_create_review_preserves_reviewer_id(self):
        response = client.post("/reviews", json=_valid_payload())
        assert response.json()["reviewer_id"] == "mgr-1"

    def test_create_review_returns_score_breakdown(self):
        response = client.post("/reviews", json=_valid_payload())
        body = response.json()
        assert body["score"]["per_criterion"] == {"technical_skill": 5, "communication": 4}
        assert body["score"]["average"] == 4.5

    def test_create_review_returns_bias_checks_for_each_commented_criterion(self):
        response = client.post("/reviews", json=_valid_payload())
        body = response.json()
        assert "technical_skill" in body["bias_checks"]
        assert "communication" in body["bias_checks"]

    def test_create_review_flags_biased_comment(self):
        payload = _valid_payload(criteria=[
            {"criterion": "technical_skill", "score": 5, "comments": "Total rockstar engineer."},
        ])
        response = client.post("/reviews", json=payload)
        body = response.json()
        assert body["bias_checks"]["technical_skill"]["flagged"] is True

    def test_create_review_omits_bias_check_for_uncommented_criterion(self):
        payload = _valid_payload(criteria=[{"criterion": "growth", "score": 3}])
        response = client.post("/reviews", json=payload)
        body = response.json()
        assert "growth" not in body["bias_checks"]

    def test_create_review_unknown_criterion_returns_422(self):
        payload = _valid_payload(criteria=[{"criterion": "vibes", "score": 5}])
        response = client.post("/reviews", json=payload)
        assert response.status_code == 422

    def test_create_review_empty_criteria_returns_422(self):
        payload = _valid_payload(criteria=[])
        response = client.post("/reviews", json=payload)
        assert response.status_code == 422

    def test_create_review_empty_employee_id_returns_422(self):
        payload = _valid_payload(employee_id="")
        response = client.post("/reviews", json=payload)
        assert response.status_code == 422

    def test_create_review_score_out_of_range_returns_422(self):
        payload = _valid_payload(criteria=[{"criterion": "growth", "score": 9}])
        response = client.post("/reviews", json=payload)
        assert response.status_code == 422


# -- list ---------------------------------------------------------------------

class TestListReviews:
    def test_list_reviews_returns_200(self):
        response = client.get("/reviews")
        assert response.status_code == 200

    def test_list_reviews_returns_list(self):
        response = client.get("/reviews")
        assert isinstance(response.json(), list)

    def test_created_review_appears_in_list(self):
        create_response = client.post("/reviews", json=_valid_payload())
        review_id = create_response.json()["id"]
        response = client.get("/reviews")
        ids = [r["id"] for r in response.json()]
        assert review_id in ids


# -- get by id ----------------------------------------------------------------

class TestGetReview:
    def test_get_existing_review_returns_200(self):
        create_response = client.post("/reviews", json=_valid_payload())
        review_id = create_response.json()["id"]
        response = client.get(f"/reviews/{review_id}")
        assert response.status_code == 200

    def test_get_review_returns_same_data_as_create(self):
        create_response = client.post("/reviews", json=_valid_payload())
        created = create_response.json()
        response = client.get(f"/reviews/{created['id']}")
        assert response.json() == created

    def test_get_unknown_review_returns_404(self):
        response = client.get("/reviews/99999")
        assert response.status_code == 404


# -- rubric (criteria catalog the frontend builds its form from) -------------

class TestGetRubric:
    def test_get_rubric_returns_200(self):
        response = client.get("/reviews/rubric")
        assert response.status_code == 200

    def test_get_rubric_includes_all_criteria_keys(self):
        response = client.get("/reviews/rubric")
        keys = {c["key"] for c in response.json()["criteria"]}
        assert keys == {"technical_skill", "communication", "collaboration", "ownership", "growth"}

    def test_get_rubric_includes_description_for_each_criterion(self):
        response = client.get("/reviews/rubric")
        for c in response.json()["criteria"]:
            assert c["description"].strip()

    def test_get_rubric_includes_score_bounds(self):
        response = client.get("/reviews/rubric")
        body = response.json()
        assert body["min_score"] == 1
        assert body["max_score"] == 5


# -- check-bias (live precheck, no review recorded) ---------------------------

class TestCheckBias:
    def test_check_bias_returns_200(self):
        response = client.post("/reviews/check-bias", json={"text": "Solid performer."})
        assert response.status_code == 200

    def test_check_bias_clean_text_not_flagged(self):
        response = client.post("/reviews/check-bias", json={"text": "Demonstrated strong technical skills."})
        assert response.json()["flagged"] is False

    def test_check_bias_biased_text_is_flagged(self):
        response = client.post("/reviews/check-bias", json={"text": "Such a ninja with the codebase."})
        assert response.json()["flagged"] is True

    def test_check_bias_does_not_create_a_review(self):
        before = client.get("/reviews").json()
        client.post("/reviews/check-bias", json={"text": "Not a culture fit."})
        after = client.get("/reviews").json()
        assert len(after) == len(before)

    def test_check_bias_response_includes_flagged_phrases(self):
        response = client.post("/reviews/check-bias", json={"text": "Not a culture fit."})
        body = response.json()
        assert len(body["flagged_phrases"]) > 0
        phrase_obj = body["flagged_phrases"][0]
        assert "phrase" in phrase_obj
        assert "suggestion" in phrase_obj
