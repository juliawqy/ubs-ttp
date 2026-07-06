"""
Domain models for the analytics service.
Dataclasses own internal state; Pydantic models are API response schemas.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pydantic import BaseModel


# ── Enums ──────────────────────────────────────────────────────────────────────

class PipelineStage(str, Enum):
    APPLIED = "applied"
    INTERVIEWED = "interviewed"
    OFFERED = "offered"
    HIRED = "hired"


class DemographicGroup(str, Enum):
    FEMALE = "female"
    MALE = "male"
    NON_BINARY = "non_binary"
    UNSPECIFIED = "unspecified"


class IncidentService(str, Enum):
    RECRUITMENT = "recruitment"
    PERFORMANCE = "performance"
    TRAINING = "training"


# ── Domain dataclasses ─────────────────────────────────────────────────────────

@dataclass
class PipelineEvent:
    """A single candidate moving through a stage of the hiring pipeline."""
    id: int
    stage: PipelineStage
    demographic_group: DemographicGroup
    timestamp: datetime


@dataclass
class BiasIncidentEvent:
    """A bias flag raised by any service (recruitment, performance, training)."""
    id: int
    service: IncidentService
    flagged: bool
    timestamp: datetime


# ── Pydantic response schemas ──────────────────────────────────────────────────

class FunnelStage(BaseModel):
    stage: str
    total: int
    diverse_pct: float


class DiversityResponse(BaseModel):
    total_applicants: int
    sourcing_diversity_ratio: float
    offer_acceptance_rate: float
    stages: dict[str, dict[str, int]]
    funnel: list[FunnelStage]


class TrendPoint(BaseModel):
    period: str   # ISO week string e.g. "2025-W12"
    count: int


class BiasIncidentsResponse(BaseModel):
    total: int
    by_service: dict[str, int]
    trend: list[TrendPoint]


class PipelineEventIn(BaseModel):
    stage: PipelineStage
    demographic_group: DemographicGroup
    timestamp: datetime | None = None


class BiasIncidentIn(BaseModel):
    service: IncidentService
    flagged: bool = True
    timestamp: datetime | None = None
