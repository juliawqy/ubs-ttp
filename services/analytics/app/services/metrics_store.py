"""
MetricsStore — single-responsibility in-memory store for analytics events.
Pre-seeded with realistic demo data on construction.
Other services inject this via constructor (DIP).
"""
from __future__ import annotations
from datetime import datetime, timedelta
from app.models import (
    PipelineEvent, BiasIncidentEvent,
    PipelineStage, DemographicGroup, IncidentService,
)

# ── Seed definitions ───────────────────────────────────────────────────────────

# (stage, group, count)
_PIPELINE_SEED = [
    (PipelineStage.APPLIED,      DemographicGroup.FEMALE,      38),
    (PipelineStage.APPLIED,      DemographicGroup.MALE,        45),
    (PipelineStage.APPLIED,      DemographicGroup.NON_BINARY,  10),
    (PipelineStage.APPLIED,      DemographicGroup.UNSPECIFIED,  7),
    (PipelineStage.INTERVIEWED,  DemographicGroup.FEMALE,      18),
    (PipelineStage.INTERVIEWED,  DemographicGroup.MALE,        22),
    (PipelineStage.INTERVIEWED,  DemographicGroup.NON_BINARY,   5),
    (PipelineStage.INTERVIEWED,  DemographicGroup.UNSPECIFIED,  2),
    (PipelineStage.OFFERED,      DemographicGroup.FEMALE,       7),
    (PipelineStage.OFFERED,      DemographicGroup.MALE,         9),
    (PipelineStage.OFFERED,      DemographicGroup.NON_BINARY,   2),
    (PipelineStage.HIRED,        DemographicGroup.FEMALE,       4),
    (PipelineStage.HIRED,        DemographicGroup.MALE,         6),
    (PipelineStage.HIRED,        DemographicGroup.NON_BINARY,   1),
]

# (weeks_ago, service, count) — spread over the past 12 weeks
_BIAS_SEED = [
    (12, IncidentService.RECRUITMENT, 3), (12, IncidentService.PERFORMANCE, 2), (12, IncidentService.TRAINING, 1),
    (11, IncidentService.RECRUITMENT, 2), (11, IncidentService.PERFORMANCE, 1), (11, IncidentService.TRAINING, 1),
    (10, IncidentService.RECRUITMENT, 3), (10, IncidentService.PERFORMANCE, 1), (10, IncidentService.TRAINING, 1),
    ( 9, IncidentService.RECRUITMENT, 2), ( 9, IncidentService.PERFORMANCE, 1),
    ( 8, IncidentService.RECRUITMENT, 2), ( 8, IncidentService.PERFORMANCE, 2),
    ( 7, IncidentService.RECRUITMENT, 1), ( 7, IncidentService.PERFORMANCE, 1),
    ( 6, IncidentService.RECRUITMENT, 2), ( 6, IncidentService.PERFORMANCE, 2), ( 6, IncidentService.TRAINING, 1),
    ( 5, IncidentService.RECRUITMENT, 2), ( 5, IncidentService.PERFORMANCE, 1), ( 5, IncidentService.TRAINING, 1),
    ( 4, IncidentService.RECRUITMENT, 1), ( 4, IncidentService.PERFORMANCE, 2),
    ( 3, IncidentService.RECRUITMENT, 3), ( 3, IncidentService.PERFORMANCE, 2), ( 3, IncidentService.TRAINING, 1),
    ( 2, IncidentService.RECRUITMENT, 2), ( 2, IncidentService.PERFORMANCE, 1), ( 2, IncidentService.TRAINING, 1),
    ( 1, IncidentService.RECRUITMENT, 2),                                       ( 1, IncidentService.TRAINING, 1),
]


class MetricsStore:
    """
    In-memory store for pipeline and bias incident events.

    Seeded with representative demo data on construction so the dashboard
    is populated immediately without requiring real service integrations.

    Args: none — seed data is always loaded. Call clear() to wipe for tests.
    """

    def __init__(self) -> None:
        self._pipeline_events: list[PipelineEvent] = []
        self._bias_incidents: list[BiasIncidentEvent] = []
        self._next_pipeline_id = 1
        self._next_incident_id = 1
        self._seed()

    # ── Public API ─────────────────────────────────────────────────────────────

    def add_pipeline_event(
        self,
        stage: PipelineStage,
        group: DemographicGroup,
        timestamp: datetime | None = None,
    ) -> PipelineEvent:
        event = PipelineEvent(
            id=self._next_pipeline_id,
            stage=stage,
            demographic_group=group,
            timestamp=timestamp or datetime.utcnow(),
        )
        self._pipeline_events.append(event)
        self._next_pipeline_id += 1
        return event

    def add_bias_incident(
        self,
        service: IncidentService,
        flagged: bool = True,
        timestamp: datetime | None = None,
    ) -> BiasIncidentEvent:
        incident = BiasIncidentEvent(
            id=self._next_incident_id,
            service=service,
            flagged=flagged,
            timestamp=timestamp or datetime.utcnow(),
        )
        self._bias_incidents.append(incident)
        self._next_incident_id += 1
        return incident

    def get_pipeline_events(self) -> list[PipelineEvent]:
        return list(self._pipeline_events)

    def get_bias_incidents(self) -> list[BiasIncidentEvent]:
        return list(self._bias_incidents)

    def clear(self) -> None:
        """Wipe all events (used in tests to start from a clean state)."""
        self._pipeline_events = []
        self._bias_incidents = []
        self._next_pipeline_id = 1
        self._next_incident_id = 1

    # ── Seed ───────────────────────────────────────────────────────────────────

    def _seed(self) -> None:
        """Populate store with realistic demo data spread over the past 12 weeks."""
        now = datetime.utcnow()

        for stage, group, count in _PIPELINE_SEED:
            for offset in range(count):
                # Spread events across the 12-week window for realism
                ts = now - timedelta(weeks=12) + timedelta(days=offset * 2)
                self.add_pipeline_event(stage=stage, group=group, timestamp=ts)

        # Calculate start of each ISO week so trend groups correctly
        today = now.date()
        monday_this_week = today - timedelta(days=today.weekday())

        for weeks_ago, service, count in _BIAS_SEED:
            week_monday = monday_this_week - timedelta(weeks=weeks_ago - 1)
            for day_offset in range(count):
                ts = datetime(week_monday.year, week_monday.month, week_monday.day,
                              9, 0, 0) + timedelta(days=day_offset)
                self.add_bias_incident(service=service, flagged=True, timestamp=ts)
