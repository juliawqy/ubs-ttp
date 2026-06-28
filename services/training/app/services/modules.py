"""
Training modules service -- validates module-assignment requests before
they are persisted. The router owns storage and id assignment; this
service owns business rules only.
"""
from dataclasses import dataclass
from datetime import date
from shared.base.service import BaseService


@dataclass
class ModuleRequest:
    title: str
    assigned_to: str
    due_date: date
    description: str = ""


@dataclass
class ModuleResult:
    title: str
    assigned_to: str
    due_date: date
    description: str
    completion_pct: float
    status: str


class TrainingModuleService(BaseService):
    """Creates and updates training module assignments."""

    def create(self, request: ModuleRequest) -> ModuleResult:
        """
        Raises:
            ValueError: if title, assigned_to, or due_date is missing
        """
        self._validate(request)
        return ModuleResult(
            title=request.title,
            assigned_to=request.assigned_to,
            due_date=request.due_date,
            description=request.description,
            completion_pct=0.0,
            status="not_started",
        )

    def update(self, request: ModuleRequest, *, completion_pct: float, status: str) -> ModuleResult:
        """
        Updates title/assignee/due date/description while preserving the
        progress state passed in -- editing a module must not reset progress.

        Raises:
            ValueError: if title, assigned_to, or due_date is missing
        """
        self._validate(request)
        return ModuleResult(
            title=request.title,
            assigned_to=request.assigned_to,
            due_date=request.due_date,
            description=request.description,
            completion_pct=completion_pct,
            status=status,
        )

    # -- internals ------------------------------------------------------------

    def _validate(self, request: ModuleRequest) -> None:
        if not request.title.strip():
            raise ValueError("title cannot be empty")
        if not request.assigned_to.strip():
            raise ValueError("assigned_to cannot be empty")
        if request.due_date is None:
            raise ValueError("due_date is required")
