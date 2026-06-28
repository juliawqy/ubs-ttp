"""
Unit tests for CareerPathService.
Run: pytest services/training/tests/unit/test_career_mapping_service.py -v
"""
from datetime import date
import pytest
from app.services.career_mapping import CareerPathService, CareerPathRequest, CareerPathResult


class FakeRecommendationEngine:
    """Stand-in collaborator -- proves CareerPathService depends on an
    injected abstraction rather than constructing RecommendationEngine itself."""

    def __init__(self, skills):
        self._skills = skills
        self.calls = []

    def recommend(self, current_role, next_milestone):
        self.calls.append((current_role, next_milestone))
        return list(self._skills)


@pytest.fixture
def fake_engine():
    return FakeRecommendationEngine(["Mock Skill A", "Mock Skill B"])


@pytest.fixture
def service(fake_engine):
    return CareerPathService(recommendation_engine=fake_engine)


@pytest.fixture
def valid_request():
    return CareerPathRequest(
        employee_name="Jane Doe",
        current_role="Software Engineer",
        next_milestone="Senior Software Engineer",
        target_date=date(2027, 1, 1),
    )


class TestCreateEntry:
    def test_returns_career_path_result_type(self, service, valid_request):
        result = service.create_entry(valid_request)
        assert isinstance(result, CareerPathResult)

    def test_preserves_employee_name(self, service, valid_request):
        result = service.create_entry(valid_request)
        assert result.employee_name == valid_request.employee_name

    def test_preserves_roles_and_target_date(self, service, valid_request):
        result = service.create_entry(valid_request)
        assert result.current_role == valid_request.current_role
        assert result.next_milestone == valid_request.next_milestone
        assert result.target_date == valid_request.target_date

    def test_uses_recommendation_engine_for_skills(self, service, valid_request):
        result = service.create_entry(valid_request)
        assert result.recommended_skills == ["Mock Skill A", "Mock Skill B"]

    def test_delegates_to_injected_engine_with_correct_args(self, service, valid_request, fake_engine):
        service.create_entry(valid_request)
        assert fake_engine.calls == [("Software Engineer", "Senior Software Engineer")]

    def test_defaults_to_real_engine_when_none_injected(self):
        service = CareerPathService()
        request = CareerPathRequest(
            employee_name="John",
            current_role="Analyst",
            next_milestone="Senior Analyst",
            target_date=date(2027, 1, 1),
        )
        result = service.create_entry(request)
        assert "Advanced Excel" in result.recommended_skills


class TestValidation:
    def test_empty_employee_name_raises(self, service, valid_request):
        valid_request.employee_name = ""
        with pytest.raises(ValueError, match="employee_name"):
            service.create_entry(valid_request)

    def test_empty_current_role_raises(self, service, valid_request):
        valid_request.current_role = ""
        with pytest.raises(ValueError, match="current_role"):
            service.create_entry(valid_request)

    def test_empty_next_milestone_raises(self, service, valid_request):
        valid_request.next_milestone = ""
        with pytest.raises(ValueError, match="next_milestone"):
            service.create_entry(valid_request)

    def test_missing_target_date_raises(self, service, valid_request):
        valid_request.target_date = None
        with pytest.raises(ValueError, match="target_date"):
            service.create_entry(valid_request)
