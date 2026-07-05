"""
Unit tests for BiasIncidentService.
Verifies bias incident aggregation and trend computation.
Run: pytest services/analytics/tests/unit/test_bias_incident_service.py -v
"""
import pytest
from datetime import datetime, timedelta
from app.services.metrics_store import MetricsStore
from app.services.bias_incident import BiasIncidentService
from app.models import IncidentService, BiasIncidentsResponse


@pytest.fixture
def service():
    return BiasIncidentService(store=MetricsStore())


@pytest.fixture
def empty_service():
    store = MetricsStore()
    store.clear()
    return BiasIncidentService(store=store)


class TestGetIncidents:
    def test_returns_bias_incidents_response_type(self, service):
        result = service.get_incidents()
        assert isinstance(result, BiasIncidentsResponse)

    def test_total_is_non_negative_integer(self, service):
        result = service.get_incidents()
        assert isinstance(result.total, int)
        assert result.total >= 0

    def test_total_counts_only_flagged_incidents(self):
        store = MetricsStore()
        store.clear()
        store.add_bias_incident(IncidentService.RECRUITMENT, flagged=True)
        store.add_bias_incident(IncidentService.RECRUITMENT, flagged=True)
        store.add_bias_incident(IncidentService.RECRUITMENT, flagged=False)
        svc = BiasIncidentService(store=store)
        result = svc.get_incidents()
        assert result.total == 2

    def test_by_service_has_all_three_keys(self, service):
        result = service.get_incidents()
        assert "recruitment" in result.by_service
        assert "performance" in result.by_service
        assert "training" in result.by_service

    def test_by_service_counts_are_non_negative(self, service):
        result = service.get_incidents()
        for count in result.by_service.values():
            assert count >= 0

    def test_by_service_sums_to_total(self, service):
        result = service.get_incidents()
        assert sum(result.by_service.values()) == result.total

    def test_trend_is_a_list(self, service):
        result = service.get_incidents()
        assert isinstance(result.trend, list)

    def test_trend_items_have_period_and_count(self, service):
        result = service.get_incidents()
        for point in result.trend:
            assert hasattr(point, "period")
            assert hasattr(point, "count")

    def test_trend_counts_are_non_negative(self, service):
        result = service.get_incidents()
        for point in result.trend:
            assert point.count >= 0

    def test_trend_is_sorted_chronologically(self, service):
        result = service.get_incidents()
        periods = [p.period for p in result.trend]
        assert periods == sorted(periods)

    def test_trend_has_at_least_one_period_with_seed_data(self, service):
        result = service.get_incidents()
        assert len(result.trend) >= 1


class TestEmptyStore:
    def test_empty_store_has_zero_total(self, empty_service):
        result = empty_service.get_incidents()
        assert result.total == 0

    def test_empty_store_by_service_all_zero(self, empty_service):
        result = empty_service.get_incidents()
        for count in result.by_service.values():
            assert count == 0

    def test_empty_store_trend_is_empty_list(self, empty_service):
        result = empty_service.get_incidents()
        assert result.trend == []


class TestAddAndQuery:
    def test_newly_added_incident_appears_in_total(self, empty_service):
        empty_service._store.add_bias_incident(IncidentService.RECRUITMENT, flagged=True)
        result = empty_service.get_incidents()
        assert result.total == 1

    def test_newly_added_incident_appears_in_by_service(self, empty_service):
        empty_service._store.add_bias_incident(IncidentService.PERFORMANCE, flagged=True)
        result = empty_service.get_incidents()
        assert result.by_service["performance"] == 1

    def test_newly_added_incident_appears_in_trend(self, empty_service):
        empty_service._store.add_bias_incident(IncidentService.TRAINING, flagged=True)
        result = empty_service.get_incidents()
        total_in_trend = sum(p.count for p in result.trend)
        assert total_in_trend == 1
