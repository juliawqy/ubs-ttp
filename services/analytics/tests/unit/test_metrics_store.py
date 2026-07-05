"""
Unit tests for MetricsStore.
Verifies storage, seed data, and event accumulation.
Run: pytest services/analytics/tests/unit/test_metrics_store.py -v
"""
import pytest
from datetime import datetime
from app.services.metrics_store import MetricsStore
from app.models import PipelineStage, DemographicGroup, IncidentService, PipelineEvent, BiasIncidentEvent


@pytest.fixture
def empty_store():
    """A store with seed data cleared — tests raw add behaviour."""
    s = MetricsStore()
    s.clear()
    return s


@pytest.fixture
def seeded_store():
    return MetricsStore()


class TestSeedData:
    def test_store_initialises_with_pipeline_events(self, seeded_store):
        events = seeded_store.get_pipeline_events()
        assert len(events) > 0

    def test_store_initialises_with_bias_incidents(self, seeded_store):
        incidents = seeded_store.get_bias_incidents()
        assert len(incidents) > 0

    def test_seed_covers_all_four_pipeline_stages(self, seeded_store):
        stages = {e.stage for e in seeded_store.get_pipeline_events()}
        assert stages == {PipelineStage.APPLIED, PipelineStage.INTERVIEWED,
                          PipelineStage.OFFERED, PipelineStage.HIRED}

    def test_seed_covers_all_three_incident_services(self, seeded_store):
        services = {i.service for i in seeded_store.get_bias_incidents()}
        assert services == {IncidentService.RECRUITMENT, IncidentService.PERFORMANCE,
                            IncidentService.TRAINING}

    def test_applied_stage_is_largest_in_funnel(self, seeded_store):
        events = seeded_store.get_pipeline_events()
        counts = {}
        for e in events:
            counts[e.stage] = counts.get(e.stage, 0) + 1
        assert counts[PipelineStage.APPLIED] > counts[PipelineStage.HIRED]


class TestAddPipelineEvent:
    def test_returns_pipeline_event_instance(self, empty_store):
        result = empty_store.add_pipeline_event(
            stage=PipelineStage.APPLIED,
            group=DemographicGroup.FEMALE,
        )
        assert isinstance(result, PipelineEvent)

    def test_event_has_correct_stage(self, empty_store):
        result = empty_store.add_pipeline_event(
            stage=PipelineStage.INTERVIEWED,
            group=DemographicGroup.MALE,
        )
        assert result.stage == PipelineStage.INTERVIEWED

    def test_event_has_correct_group(self, empty_store):
        result = empty_store.add_pipeline_event(
            stage=PipelineStage.OFFERED,
            group=DemographicGroup.NON_BINARY,
        )
        assert result.demographic_group == DemographicGroup.NON_BINARY

    def test_event_receives_auto_timestamp_when_none_given(self, empty_store):
        result = empty_store.add_pipeline_event(
            stage=PipelineStage.HIRED,
            group=DemographicGroup.FEMALE,
        )
        assert isinstance(result.timestamp, datetime)

    def test_custom_timestamp_is_stored(self, empty_store):
        ts = datetime(2025, 6, 1, 12, 0, 0)
        result = empty_store.add_pipeline_event(
            stage=PipelineStage.APPLIED,
            group=DemographicGroup.MALE,
            timestamp=ts,
        )
        assert result.timestamp == ts

    def test_add_increases_count_by_one(self, empty_store):
        before = len(empty_store.get_pipeline_events())
        empty_store.add_pipeline_event(PipelineStage.APPLIED, DemographicGroup.FEMALE)
        after = len(empty_store.get_pipeline_events())
        assert after == before + 1

    def test_successive_events_have_unique_ids(self, empty_store):
        e1 = empty_store.add_pipeline_event(PipelineStage.APPLIED, DemographicGroup.FEMALE)
        e2 = empty_store.add_pipeline_event(PipelineStage.APPLIED, DemographicGroup.MALE)
        assert e1.id != e2.id


class TestAddBiasIncident:
    def test_returns_bias_incident_event_instance(self, empty_store):
        result = empty_store.add_bias_incident(service=IncidentService.RECRUITMENT)
        assert isinstance(result, BiasIncidentEvent)

    def test_incident_has_correct_service(self, empty_store):
        result = empty_store.add_bias_incident(service=IncidentService.PERFORMANCE)
        assert result.service == IncidentService.PERFORMANCE

    def test_flagged_defaults_to_true(self, empty_store):
        result = empty_store.add_bias_incident(service=IncidentService.TRAINING)
        assert result.flagged is True

    def test_flagged_false_can_be_stored(self, empty_store):
        result = empty_store.add_bias_incident(
            service=IncidentService.RECRUITMENT, flagged=False
        )
        assert result.flagged is False

    def test_add_increases_count_by_one(self, empty_store):
        before = len(empty_store.get_bias_incidents())
        empty_store.add_bias_incident(IncidentService.RECRUITMENT)
        after = len(empty_store.get_bias_incidents())
        assert after == before + 1


class TestClear:
    def test_clear_empties_pipeline_events(self, seeded_store):
        seeded_store.clear()
        assert seeded_store.get_pipeline_events() == []

    def test_clear_empties_bias_incidents(self, seeded_store):
        seeded_store.clear()
        assert seeded_store.get_bias_incidents() == []

    def test_events_added_after_clear_are_retained(self, seeded_store):
        seeded_store.clear()
        seeded_store.add_pipeline_event(PipelineStage.APPLIED, DemographicGroup.FEMALE)
        assert len(seeded_store.get_pipeline_events()) == 1
