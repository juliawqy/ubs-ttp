"""
Metrics router — analytics API endpoints.
Owns HTTP only; all business logic lives in the injected services (DIP).
"""
from __future__ import annotations
from typing import Annotated
from fastapi import APIRouter, Depends
from app.models import (
    DiversityResponse, BiasIncidentsResponse,
    PipelineEventIn, BiasIncidentIn,
    PipelineEvent, BiasIncidentEvent,
)
from app.services.metrics_store import MetricsStore
from app.services.diversity_metrics import DiversityMetricsService
from app.services.bias_incident import BiasIncidentService

router = APIRouter(prefix="/metrics", tags=["metrics"])

# ── Module-level singleton (reset in tests via conftest) ───────────────────────
_store = MetricsStore()


# ── Dependency factories ───────────────────────────────────────────────────────

def get_store() -> MetricsStore:
    return _store


def get_diversity_service() -> DiversityMetricsService:
    return DiversityMetricsService(store=_store)


def get_bias_service() -> BiasIncidentService:
    return BiasIncidentService(store=_store)


# ── Read endpoints ─────────────────────────────────────────────────────────────

@router.get(
    "/diversity",
    response_model=DiversityResponse,
    responses={200: {"description": "Pipeline diversity breakdown by stage and demographic group"}},
)
def get_diversity(
    svc: Annotated[DiversityMetricsService, Depends(get_diversity_service)],
) -> DiversityResponse:
    """TTP-28: Pipeline diversity stats by stage (applied, interviewed, offered, hired)."""
    return svc.get_diversity()


@router.get(
    "/bias-incidents",
    response_model=BiasIncidentsResponse,
    responses={200: {"description": "Bias incident counts aggregated across services with weekly trend"}},
)
def get_bias_incidents(
    svc: Annotated[BiasIncidentService, Depends(get_bias_service)],
) -> BiasIncidentsResponse:
    """TTP-29: Bias incident tracking — aggregated across all services with trend over time."""
    return svc.get_incidents()


@router.get(
    "/kpis",
    responses={200: {"description": "Combined KPI summary for the analytics dashboard"}},
)
def get_kpis(
    diversity_svc: Annotated[DiversityMetricsService, Depends(get_diversity_service)],
    bias_svc: Annotated[BiasIncidentService, Depends(get_bias_service)],
) -> dict:
    """
    TTP-30: Combined KPI data for the dashboard frontend.
    Returns all data needed in a single call to minimise round-trips.
    """
    diversity = diversity_svc.get_diversity()
    incidents = bias_svc.get_incidents()

    return {
        # KPI tiles
        "sourcing_diversity_ratio": diversity.sourcing_diversity_ratio,
        "skills_hire_rate": diversity.skills_hire_rate,
        "avg_promotion_months": 14.2,   # seeded static — extend when HR data integrated
        "enps_score": 42,               # seeded static — extend when survey data integrated
        # Chart data
        "pipeline_by_stage": [
            {"stage": f.stage, "total": f.total, "pct": f.diverse_pct}
            for f in diversity.funnel
        ],
        "bias_incidents_trend": [
            {"period": p.period, "count": p.count}
            for p in incidents.trend
        ],
        "training_completion_by_group": [
            {"group": "female",      "pct": 76.4},
            {"group": "male",        "pct": 79.2},
            {"group": "non_binary",  "pct": 80.0},
            {"group": "unspecified", "pct": 60.0},
        ],
    }


# ── Write endpoints (internal — called by other services) ─────────────────────

@router.post(
    "/pipeline-event",
    status_code=201,
    responses={
        201: {"description": "Pipeline event recorded"},
        422: {"description": "Invalid stage or demographic group"},
    },
)
def record_pipeline_event(
    body: PipelineEventIn,
    store: Annotated[MetricsStore, Depends(get_store)],
) -> dict:
    """Record a candidate progressing through a pipeline stage."""
    event: PipelineEvent = store.add_pipeline_event(
        stage=body.stage,
        group=body.demographic_group,
        timestamp=body.timestamp,
    )
    return {
        "id": event.id,
        "stage": event.stage.value,
        "demographic_group": event.demographic_group.value,
        "timestamp": event.timestamp.isoformat(),
    }


@router.post(
    "/bias-incident",
    status_code=201,
    responses={
        201: {"description": "Bias incident recorded"},
        422: {"description": "Invalid service name"},
    },
)
def record_bias_incident(
    body: BiasIncidentIn,
    store: Annotated[MetricsStore, Depends(get_store)],
) -> dict:
    """Record a bias flag raised by any service."""
    incident: BiasIncidentEvent = store.add_bias_incident(
        service=body.service,
        flagged=body.flagged,
        timestamp=body.timestamp,
    )
    return {
        "id": incident.id,
        "service": incident.service.value,
        "flagged": incident.flagged,
        "timestamp": incident.timestamp.isoformat(),
    }
