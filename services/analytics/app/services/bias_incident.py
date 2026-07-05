"""
BiasIncidentService — aggregates bias incident events across services.
Single responsibility: grouping, counting, and trend computation.
Injected into the router via constructor (DIP).
"""
from __future__ import annotations
from app.models import BiasIncidentsResponse, TrendPoint, IncidentService
from app.services.metrics_store import MetricsStore


def _iso_week(dt) -> str:
    """Return ISO week string e.g. '2025-W12' for a given datetime."""
    year, week, _ = dt.isocalendar()
    return f"{year}-W{week:02d}"


class BiasIncidentService:
    """
    Aggregates BiasIncidentEvents from MetricsStore into reportable metrics.

    Args:
        store: MetricsStore injected at construction time.
    """

    def __init__(self, store: MetricsStore) -> None:
        self._store = store

    def get_incidents(self) -> BiasIncidentsResponse:
        """
        Return total flagged incidents, per-service breakdown, and weekly trend.
        Only counts events where flagged=True.
        """
        incidents = [i for i in self._store.get_bias_incidents() if i.flagged]

        total = len(incidents)

        # Per-service counts — ensure all three keys are always present
        by_service: dict[str, int] = {svc.value: 0 for svc in IncidentService}
        for inc in incidents:
            by_service[inc.service.value] += 1

        # Weekly trend — aggregate by ISO week, sorted chronologically
        week_counts: dict[str, int] = {}
        for inc in incidents:
            key = _iso_week(inc.timestamp)
            week_counts[key] = week_counts.get(key, 0) + 1

        trend = [
            TrendPoint(period=period, count=count)
            for period, count in sorted(week_counts.items())
        ]

        return BiasIncidentsResponse(
            total=total,
            by_service=by_service,
            trend=trend,
        )
