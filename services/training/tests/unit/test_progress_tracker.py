"""
Unit tests for ProgressTrackerService.
Run: pytest services/training/tests/unit/test_progress_tracker.py -v
"""
from datetime import date, timedelta
import pytest
from app.models import TrainingModule
from app.services.progress_tracker import ProgressTrackerService

TODAY = date(2026, 6, 21)


def _module(**overrides) -> TrainingModule:
    defaults = dict(
        id=1,
        title="Anti-Bias Fundamentals",
        assigned_to="Jane Doe",
        due_date=TODAY + timedelta(days=10),
        completion_pct=0.0,
        status="not_started",
    )
    defaults.update(overrides)
    return TrainingModule(**defaults)


@pytest.fixture
def tracker():
    return ProgressTrackerService(reminder_window_days=3)


class TestUpdateCompletion:
    def test_zero_pct_sets_not_started(self, tracker):
        result = tracker.update_completion(_module(), 0)
        assert result.status == "not_started"

    def test_partial_pct_sets_in_progress(self, tracker):
        result = tracker.update_completion(_module(), 45)
        assert result.status == "in_progress"

    def test_full_pct_sets_completed(self, tracker):
        result = tracker.update_completion(_module(), 100)
        assert result.status == "completed"

    def test_completion_pct_is_stored(self, tracker):
        result = tracker.update_completion(_module(), 45)
        assert result.completion_pct == 45

    def test_does_not_mutate_original(self, tracker):
        original = _module(completion_pct=0)
        tracker.update_completion(original, 100)
        assert original.completion_pct == 0

    def test_negative_pct_raises(self, tracker):
        with pytest.raises(ValueError, match="completion_pct"):
            tracker.update_completion(_module(), -1)

    def test_pct_above_100_raises(self, tracker):
        with pytest.raises(ValueError, match="completion_pct"):
            tracker.update_completion(_module(), 101)

    def test_boundary_zero_is_valid(self, tracker):
        result = tracker.update_completion(_module(), 0)
        assert result.completion_pct == 0

    def test_boundary_100_is_valid(self, tracker):
        result = tracker.update_completion(_module(), 100)
        assert result.completion_pct == 100


class TestOverdue:
    def test_past_due_date_is_overdue(self, tracker):
        module = _module(due_date=TODAY - timedelta(days=1))
        assert tracker.is_overdue(module, TODAY) is True

    def test_future_due_date_is_not_overdue(self, tracker):
        module = _module(due_date=TODAY + timedelta(days=1))
        assert tracker.is_overdue(module, TODAY) is False

    def test_due_today_is_not_overdue(self, tracker):
        module = _module(due_date=TODAY)
        assert tracker.is_overdue(module, TODAY) is False

    def test_completed_module_is_never_overdue(self, tracker):
        module = _module(due_date=TODAY - timedelta(days=5), status="completed")
        assert tracker.is_overdue(module, TODAY) is False


class TestDueSoon:
    def test_within_window_is_due_soon(self, tracker):
        module = _module(due_date=TODAY + timedelta(days=2))
        assert tracker.is_due_soon(module, TODAY) is True

    def test_outside_window_is_not_due_soon(self, tracker):
        module = _module(due_date=TODAY + timedelta(days=10))
        assert tracker.is_due_soon(module, TODAY) is False

    def test_due_today_is_due_soon(self, tracker):
        module = _module(due_date=TODAY)
        assert tracker.is_due_soon(module, TODAY) is True

    def test_completed_module_is_never_due_soon(self, tracker):
        module = _module(due_date=TODAY, status="completed")
        assert tracker.is_due_soon(module, TODAY) is False

    def test_window_is_injectable(self):
        """OCP: the due-soon window is a constructor parameter, not a hardcoded constant."""
        wide_tracker = ProgressTrackerService(reminder_window_days=14)
        module = _module(due_date=TODAY + timedelta(days=10))
        assert wide_tracker.is_due_soon(module, TODAY) is True


class TestShouldRemind:
    def test_overdue_module_should_remind(self, tracker):
        module = _module(due_date=TODAY - timedelta(days=1))
        assert tracker.should_remind(module, TODAY) is True

    def test_due_soon_module_should_remind(self, tracker):
        module = _module(due_date=TODAY + timedelta(days=1))
        assert tracker.should_remind(module, TODAY) is True

    def test_not_due_module_should_not_remind(self, tracker):
        module = _module(due_date=TODAY + timedelta(days=30))
        assert tracker.should_remind(module, TODAY) is False

    def test_completed_module_should_never_remind(self, tracker):
        module = _module(due_date=TODAY - timedelta(days=5), status="completed")
        assert tracker.should_remind(module, TODAY) is False
