"""
Progress tracker -- updates a training module's completion percentage and
decides whether a reminder is due. Status always derives from completion_pct
so the two values can never disagree.
"""
from dataclasses import replace
from datetime import date
from shared.base.service import BaseService
from app.models import TrainingModule

NOT_STARTED = "not_started"
IN_PROGRESS = "in_progress"
COMPLETED = "completed"

DEFAULT_REMINDER_WINDOW_DAYS = 3


class ProgressTrackerService(BaseService):
    """
    OCP: reminder_window_days is injectable so the "due soon" threshold can
    change without modifying this class.
    """

    def __init__(self, reminder_window_days: int = DEFAULT_REMINDER_WINDOW_DAYS):
        self._reminder_window_days = reminder_window_days

    def update_completion(self, module: TrainingModule, completion_pct: float) -> TrainingModule:
        """
        Returns a new TrainingModule with completion_pct and a derived status.

        Raises:
            ValueError: completion_pct outside [0, 100]
        """
        if not 0 <= completion_pct <= 100:
            raise ValueError("completion_pct must be between 0 and 100")

        return replace(
            module,
            completion_pct=completion_pct,
            status=self._derive_status(completion_pct),
        )

    def is_overdue(self, module: TrainingModule, today: date) -> bool:
        return module.status != COMPLETED and module.due_date < today

    def is_due_soon(self, module: TrainingModule, today: date) -> bool:
        if module.status == COMPLETED:
            return False
        days_remaining = (module.due_date - today).days
        return 0 <= days_remaining <= self._reminder_window_days

    def should_remind(self, module: TrainingModule, today: date) -> bool:
        return self.is_overdue(module, today) or self.is_due_soon(module, today)

    def _derive_status(self, completion_pct: float) -> str:
        if completion_pct >= 100:
            return COMPLETED
        if completion_pct > 0:
            return IN_PROGRESS
        return NOT_STARTED
