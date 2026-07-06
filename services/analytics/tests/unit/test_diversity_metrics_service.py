"""
Unit tests for DiversityMetricsService.
Verifies pipeline funnel computation and diversity KPI derivation.
Run: pytest services/analytics/tests/unit/test_diversity_metrics_service.py -v
"""
import pytest
from app.services.metrics_store import MetricsStore
from app.services.diversity_metrics import DiversityMetricsService
from app.models import PipelineStage, DemographicGroup, DiversityResponse


@pytest.fixture
def service():
    return DiversityMetricsService(store=MetricsStore())


@pytest.fixture
def empty_service():
    store = MetricsStore()
    store.clear()
    return DiversityMetricsService(store=store)


class TestGetDiversity:
    def test_returns_diversity_response_type(self, service):
        result = service.get_diversity()
        assert isinstance(result, DiversityResponse)

    def test_funnel_has_four_entries(self, service):
        result = service.get_diversity()
        assert len(result.funnel) == 4

    def test_funnel_stage_order_is_applied_interviewed_offered_hired(self, service):
        result = service.get_diversity()
        stages = [f.stage for f in result.funnel]
        assert stages == ["applied", "interviewed", "offered", "hired"]

    def test_funnel_totals_decrease_from_applied_to_hired(self, service):
        result = service.get_diversity()
        totals = [f.total for f in result.funnel]
        assert totals == sorted(totals, reverse=True)

    def test_applied_total_matches_all_applied_events(self):
        store = MetricsStore()
        store.clear()
        store.add_pipeline_event(PipelineStage.APPLIED, DemographicGroup.FEMALE)
        store.add_pipeline_event(PipelineStage.APPLIED, DemographicGroup.MALE)
        store.add_pipeline_event(PipelineStage.APPLIED, DemographicGroup.NON_BINARY)
        svc = DiversityMetricsService(store=store)
        result = svc.get_diversity()
        applied_funnel = next(f for f in result.funnel if f.stage == "applied")
        assert applied_funnel.total == 3

    def test_diverse_pct_is_float_between_0_and_100(self, service):
        result = service.get_diversity()
        for funnel_stage in result.funnel:
            if funnel_stage.total > 0:
                assert 0.0 <= funnel_stage.diverse_pct <= 100.0

    def test_stages_dict_has_all_four_stages(self, service):
        result = service.get_diversity()
        assert "applied" in result.stages
        assert "interviewed" in result.stages
        assert "offered" in result.stages
        assert "hired" in result.stages

    def test_stages_breakdown_has_demographic_groups(self, service):
        result = service.get_diversity()
        applied = result.stages["applied"]
        assert isinstance(applied, dict)
        assert len(applied) > 0

    def test_total_applicants_equals_applied_count(self, service):
        result = service.get_diversity()
        applied_funnel = next(f for f in result.funnel if f.stage == "applied")
        assert result.total_applicants == applied_funnel.total


class TestEmptyStore:
    def test_empty_store_returns_zero_total_applicants(self, empty_service):
        result = empty_service.get_diversity()
        assert result.total_applicants == 0

    def test_empty_store_funnel_totals_are_all_zero(self, empty_service):
        result = empty_service.get_diversity()
        for f in result.funnel:
            assert f.total == 0

    def test_empty_store_diverse_pct_is_zero_not_nan(self, empty_service):
        result = empty_service.get_diversity()
        for f in result.funnel:
            assert f.diverse_pct == 0.0


class TestKPIValues:
    def test_sourcing_diversity_ratio_is_float_percentage(self, service):
        result = service.get_diversity()
        assert isinstance(result.sourcing_diversity_ratio, float)
        assert 0.0 <= result.sourcing_diversity_ratio <= 100.0

    def test_offer_acceptance_rate_is_float_percentage(self, service):
        result = service.get_diversity()
        assert isinstance(result.offer_acceptance_rate, float)
        assert 0.0 <= result.offer_acceptance_rate <= 100.0

    def test_offer_acceptance_rate_is_zero_when_no_offers(self, empty_service):
        empty_service._store.add_pipeline_event(PipelineStage.APPLIED, DemographicGroup.FEMALE)
        result = empty_service.get_diversity()
        assert result.offer_acceptance_rate == 0.0

    def test_offer_acceptance_rate_reflects_hired_over_offered(self):
        store = MetricsStore()
        store.clear()
        # 4 offered, 2 hired → 50%
        for _ in range(4):
            store.add_pipeline_event(PipelineStage.OFFERED, DemographicGroup.MALE)
        for _ in range(2):
            store.add_pipeline_event(PipelineStage.HIRED, DemographicGroup.MALE)
        svc = DiversityMetricsService(store=store)
        result = svc.get_diversity()
        assert result.offer_acceptance_rate == 50.0

    def test_sourcing_diversity_ratio_reflects_applied_diverse_pct(self, service):
        result = service.get_diversity()
        applied_funnel = next(f for f in result.funnel if f.stage == "applied")
        assert result.sourcing_diversity_ratio == applied_funnel.diverse_pct

    def test_non_binary_counted_as_diverse(self):
        store = MetricsStore()
        store.clear()
        store.add_pipeline_event(PipelineStage.APPLIED, DemographicGroup.NON_BINARY)
        store.add_pipeline_event(PipelineStage.APPLIED, DemographicGroup.MALE)
        svc = DiversityMetricsService(store=store)
        result = svc.get_diversity()
        assert result.sourcing_diversity_ratio == 50.0

    def test_male_not_counted_as_diverse(self):
        store = MetricsStore()
        store.clear()
        store.add_pipeline_event(PipelineStage.APPLIED, DemographicGroup.MALE)
        svc = DiversityMetricsService(store=store)
        result = svc.get_diversity()
        assert result.sourcing_diversity_ratio == 0.0
