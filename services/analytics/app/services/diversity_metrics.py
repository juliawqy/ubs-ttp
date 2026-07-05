"""
DiversityMetricsService — computes pipeline diversity statistics.
Single responsibility: aggregation of PipelineEvents from MetricsStore.
Injected into the router via constructor (DIP).
"""
from __future__ import annotations
from app.models import (
    DiversityResponse, FunnelStage,
    PipelineStage, DemographicGroup,
)
from app.services.metrics_store import MetricsStore

# Ordered pipeline stages for the funnel
_STAGE_ORDER = [
    PipelineStage.APPLIED,
    PipelineStage.INTERVIEWED,
    PipelineStage.OFFERED,
    PipelineStage.HIRED,
]

# "Diverse" = not male and not unspecified (female + non_binary)
_DIVERSE_GROUPS = {DemographicGroup.FEMALE, DemographicGroup.NON_BINARY}


class DiversityMetricsService:
    """
    Aggregates pipeline events into diversity metrics.

    Args:
        store: MetricsStore injected at construction time.
    """

    def __init__(self, store: MetricsStore) -> None:
        self._store = store

    def get_diversity(self) -> DiversityResponse:
        """
        Build a full diversity report: per-stage demographic breakdown,
        funnel totals, sourcing diversity ratio, and skills-hire rate.
        """
        events = self._store.get_pipeline_events()

        # Count events by stage and demographic group
        stage_counts: dict[PipelineStage, dict[str, int]] = {
            s: {} for s in _STAGE_ORDER
        }
        for ev in events:
            group_key = ev.demographic_group.value
            stage_counts[ev.stage][group_key] = (
                stage_counts[ev.stage].get(group_key, 0) + 1
            )

        # Build funnel list
        funnel: list[FunnelStage] = []
        for stage in _STAGE_ORDER:
            counts = stage_counts[stage]
            total = sum(counts.values())
            diverse = sum(
                counts.get(g.value, 0) for g in _DIVERSE_GROUPS
            )
            diverse_pct = round((diverse / total * 100), 1) if total > 0 else 0.0
            funnel.append(FunnelStage(
                stage=stage.value,
                total=total,
                diverse_pct=diverse_pct,
            ))

        # KPI: sourcing diversity ratio (% diverse at applied stage)
        applied_funnel = funnel[0]
        sourcing_diversity_ratio = applied_funnel.diverse_pct

        # KPI: skills-hire rate (hires / offers — proxy for bias-free decision making)
        offered_total = funnel[2].total
        hired_total = funnel[3].total
        skills_hire_rate = (
            round(hired_total / offered_total * 100, 1) if offered_total > 0 else 0.0
        )

        return DiversityResponse(
            total_applicants=applied_funnel.total,
            sourcing_diversity_ratio=sourcing_diversity_ratio,
            skills_hire_rate=skills_hire_rate,
            stages={stage.value: stage_counts[stage] for stage in _STAGE_ORDER},
            funnel=funnel,
        )
