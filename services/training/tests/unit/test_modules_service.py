"""
Unit tests for TrainingModuleService.
Run: pytest services/training/tests/unit/test_modules_service.py -v
"""
from datetime import date
import pytest
from app.services.modules import TrainingModuleService, ModuleRequest, ModuleResult


@pytest.fixture
def service():
    return TrainingModuleService()


@pytest.fixture
def valid_request():
    return ModuleRequest(
        title="Anti-Bias Fundamentals",
        assigned_to="Jane Doe",
        due_date=date(2026, 7, 1),
        description="Intro module on recognising unconscious bias.",
    )


class TestCreate:
    def test_returns_module_result_type(self, service, valid_request):
        result = service.create(valid_request)
        assert isinstance(result, ModuleResult)

    def test_status_is_not_started(self, service, valid_request):
        result = service.create(valid_request)
        assert result.status == "not_started"

    def test_completion_pct_is_zero(self, service, valid_request):
        result = service.create(valid_request)
        assert result.completion_pct == 0.0

    def test_preserves_title_and_assigned_to(self, service, valid_request):
        result = service.create(valid_request)
        assert result.title == valid_request.title
        assert result.assigned_to == valid_request.assigned_to

    def test_preserves_due_date(self, service, valid_request):
        result = service.create(valid_request)
        assert result.due_date == valid_request.due_date

    def test_preserves_description(self, service, valid_request):
        result = service.create(valid_request)
        assert result.description == valid_request.description


class TestValidation:
    def test_empty_title_raises(self, service, valid_request):
        valid_request.title = ""
        with pytest.raises(ValueError, match="title"):
            service.create(valid_request)

    def test_whitespace_title_raises(self, service, valid_request):
        valid_request.title = "   "
        with pytest.raises(ValueError, match="title"):
            service.create(valid_request)

    def test_empty_assigned_to_raises(self, service, valid_request):
        valid_request.assigned_to = ""
        with pytest.raises(ValueError, match="assigned_to"):
            service.create(valid_request)

    def test_missing_due_date_raises(self, service, valid_request):
        valid_request.due_date = None
        with pytest.raises(ValueError, match="due_date"):
            service.create(valid_request)


class TestUpdate:
    def test_update_applies_new_title(self, service, valid_request):
        result = service.update(valid_request, completion_pct=40, status="in_progress")
        assert result.title == valid_request.title

    def test_update_preserves_passed_in_progress_state(self, service, valid_request):
        result = service.update(valid_request, completion_pct=40, status="in_progress")
        assert result.completion_pct == 40
        assert result.status == "in_progress"

    def test_update_validates_like_create(self, service, valid_request):
        valid_request.title = ""
        with pytest.raises(ValueError, match="title"):
            service.update(valid_request, completion_pct=0, status="not_started")
