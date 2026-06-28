"""
Training domain models shared across router and service layers.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import date


@dataclass
class TrainingModule:
    """A training module assigned to a specific employee."""
    id: int
    title: str
    assigned_to: str
    due_date: date
    description: str = ""
    completion_pct: float = 0.0
    status: str = "not_started"      # not_started | in_progress | completed
    reminder_count: int = 0
