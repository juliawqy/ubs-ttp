"""
Unit tests for PanelAssignment.
Run: pytest services/recruitment/tests/unit/test_panel_assignment.py -v
"""
import pytest
from app.services.panel_assignment import PanelAssignmentService, Interviewer, PanelAssignment


@pytest.fixture
def diverse_pool():
    return [
        Interviewer(id="i1", name="Alex Chen", gender="male", department="engineering"),
        Interviewer(id="i2", name="Sara Patel", gender="female", department="product"),
        Interviewer(id="i3", name="James Obi", gender="male", department="engineering"),
        Interviewer(id="i4", name="Mei Lin", gender="female", department="hr"),
        Interviewer(id="i5", name="David Kim", gender="male", department="design"),
    ]


@pytest.fixture
def homogeneous_pool():
    return [
        Interviewer(id="i1", name="John Smith", gender="male", department="engineering"),
        Interviewer(id="i2", name="Mike Jones", gender="male", department="engineering"),
        Interviewer(id="i3", name="Tom Brown", gender="male", department="engineering"),
    ]


@pytest.fixture
def service():
    return PanelAssignmentService(min_panel_size=3)


class TestDiverseAssignment:
    def test_returns_panel_assignment_type(self, service, diverse_pool):
        result = service.assign(diverse_pool, panel_size=3)
        assert isinstance(result, PanelAssignment)

    def test_panel_has_correct_size(self, service, diverse_pool):
        result = service.assign(diverse_pool, panel_size=3)
        assert len(result.interviewers) == 3

    def test_diverse_panel_is_accepted(self, service, diverse_pool):
        result = service.assign(diverse_pool, panel_size=3)
        assert result.approved is True

    def test_panel_includes_gender_diversity(self, service, diverse_pool):
        result = service.assign(diverse_pool, panel_size=3)
        genders = {i.gender for i in result.interviewers}
        assert len(genders) > 1

    def test_panel_includes_department_diversity(self, service, diverse_pool):
        result = service.assign(diverse_pool, panel_size=3)
        depts = {i.department for i in result.interviewers}
        assert len(depts) > 1


class TestRejection:
    def test_all_same_gender_panel_is_rejected(self, service, homogeneous_pool):
        result = service.assign(homogeneous_pool, panel_size=3)
        assert result.approved is False

    def test_rejection_includes_reason(self, service, homogeneous_pool):
        result = service.assign(homogeneous_pool, panel_size=3)
        assert result.rejection_reason is not None
        assert result.rejection_reason != ""

    def test_all_same_department_panel_is_rejected(self, service, homogeneous_pool):
        result = service.assign(homogeneous_pool, panel_size=3)
        assert result.approved is False


class TestEdgeCases:
    def test_pool_smaller_than_panel_size_raises(self, service):
        small_pool = [
            Interviewer(id="i1", name="Alex", gender="male", department="eng"),
            Interviewer(id="i2", name="Sara", gender="female", department="product"),
        ]
        with pytest.raises(ValueError, match="pool"):
            service.assign(small_pool, panel_size=3)

    def test_panel_size_below_minimum_raises(self, service, diverse_pool):
        with pytest.raises(ValueError, match="minimum"):
            service.assign(diverse_pool, panel_size=1)

    def test_empty_pool_raises(self, service):
        with pytest.raises(ValueError, match="pool"):
            service.assign([], panel_size=3)
