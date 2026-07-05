"""
Integration tests for the /metrics API endpoints.
Uses FastAPI TestClient; the conftest resets the in-memory store before each test.
Run: pytest services/analytics/tests/integration/ -v
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models import PipelineStage, DemographicGroup, IncidentService

client = TestClient(app)


class TestHealthEndpoint:
    def test_health_returns_200(self):
        res = client.get("/health")
        assert res.status_code == 200

    def test_health_returns_ok_status(self):
        res = client.get("/health")
        assert res.json()["status"] == "ok"


class TestGetDiversityEndpoint:
    def test_returns_200(self):
        res = client.get("/metrics/diversity")
        assert res.status_code == 200

    def test_response_has_funnel_field(self):
        res = client.get("/metrics/diversity")
        data = res.json()
        assert "funnel" in data

    def test_funnel_has_four_stages(self):
        res = client.get("/metrics/diversity")
        assert len(res.json()["funnel"]) == 4

    def test_funnel_stage_names(self):
        res = client.get("/metrics/diversity")
        stages = [f["stage"] for f in res.json()["funnel"]]
        assert stages == ["applied", "interviewed", "offered", "hired"]

    def test_response_has_stages_breakdown(self):
        res = client.get("/metrics/diversity")
        assert "stages" in res.json()

    def test_response_has_total_applicants(self):
        res = client.get("/metrics/diversity")
        assert "total_applicants" in res.json()

    def test_response_has_sourcing_diversity_ratio(self):
        res = client.get("/metrics/diversity")
        assert "sourcing_diversity_ratio" in res.json()

    def test_response_has_skills_hire_rate(self):
        res = client.get("/metrics/diversity")
        assert "skills_hire_rate" in res.json()


class TestGetBiasIncidentsEndpoint:
    def test_returns_200(self):
        res = client.get("/metrics/bias-incidents")
        assert res.status_code == 200

    def test_response_has_total_field(self):
        res = client.get("/metrics/bias-incidents")
        assert "total" in res.json()

    def test_response_has_by_service_field(self):
        res = client.get("/metrics/bias-incidents")
        assert "by_service" in res.json()

    def test_response_has_trend_field(self):
        res = client.get("/metrics/bias-incidents")
        assert "trend" in res.json()

    def test_by_service_has_three_keys(self):
        res = client.get("/metrics/bias-incidents")
        by_service = res.json()["by_service"]
        assert set(by_service.keys()) == {"recruitment", "performance", "training"}

    def test_trend_items_have_period_and_count(self):
        res = client.get("/metrics/bias-incidents")
        for point in res.json()["trend"]:
            assert "period" in point
            assert "count" in point


class TestGetKPIsEndpoint:
    def test_returns_200(self):
        res = client.get("/metrics/kpis")
        assert res.status_code == 200

    def test_has_sourcing_diversity_ratio(self):
        data = client.get("/metrics/kpis").json()
        assert "sourcing_diversity_ratio" in data

    def test_has_skills_hire_rate(self):
        data = client.get("/metrics/kpis").json()
        assert "skills_hire_rate" in data

    def test_has_avg_promotion_months(self):
        data = client.get("/metrics/kpis").json()
        assert "avg_promotion_months" in data

    def test_has_enps_score(self):
        data = client.get("/metrics/kpis").json()
        assert "enps_score" in data

    def test_has_pipeline_by_stage(self):
        data = client.get("/metrics/kpis").json()
        assert "pipeline_by_stage" in data

    def test_has_bias_incidents_trend(self):
        data = client.get("/metrics/kpis").json()
        assert "bias_incidents_trend" in data

    def test_has_training_completion_by_group(self):
        data = client.get("/metrics/kpis").json()
        assert "training_completion_by_group" in data

    def test_pipeline_by_stage_has_four_entries(self):
        data = client.get("/metrics/kpis").json()
        assert len(data["pipeline_by_stage"]) == 4


class TestPostPipelineEvent:
    def test_returns_201(self):
        res = client.post("/metrics/pipeline-event", json={
            "stage": "applied",
            "demographic_group": "female",
        })
        assert res.status_code == 201

    def test_response_has_id_field(self):
        res = client.post("/metrics/pipeline-event", json={
            "stage": "applied",
            "demographic_group": "male",
        })
        assert "id" in res.json()

    def test_response_has_stage_field(self):
        res = client.post("/metrics/pipeline-event", json={
            "stage": "interviewed",
            "demographic_group": "non_binary",
        })
        assert res.json()["stage"] == "interviewed"

    def test_event_increases_diversity_count(self):
        before = client.get("/metrics/diversity").json()["total_applicants"]
        client.post("/metrics/pipeline-event", json={
            "stage": "applied",
            "demographic_group": "female",
        })
        after = client.get("/metrics/diversity").json()["total_applicants"]
        assert after == before + 1

    def test_invalid_stage_returns_422(self):
        res = client.post("/metrics/pipeline-event", json={
            "stage": "unknown_stage",
            "demographic_group": "female",
        })
        assert res.status_code == 422


class TestPostBiasIncident:
    def test_returns_201(self):
        res = client.post("/metrics/bias-incident", json={
            "service": "recruitment",
            "flagged": True,
        })
        assert res.status_code == 201

    def test_response_has_id_field(self):
        res = client.post("/metrics/bias-incident", json={
            "service": "performance",
        })
        assert "id" in res.json()

    def test_incident_increases_total(self):
        before = client.get("/metrics/bias-incidents").json()["total"]
        client.post("/metrics/bias-incident", json={
            "service": "training",
            "flagged": True,
        })
        after = client.get("/metrics/bias-incidents").json()["total"]
        assert after == before + 1

    def test_invalid_service_returns_422(self):
        res = client.post("/metrics/bias-incident", json={
            "service": "unknown_service",
        })
        assert res.status_code == 422
