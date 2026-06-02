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


class TestBoundaryValues:
    def test_pool_exactly_equal_to_panel_size(self, service):
        """Pool with exactly 3 diverse interviewers should work."""
        exact_pool = [
            Interviewer(id="i1", name="Alex", gender="male", department="engineering"),
            Interviewer(id="i2", name="Sara", gender="female", department="product"),
            Interviewer(id="i3", name="James", gender="male", department="hr"),
        ]
        result = service.assign(exact_pool, panel_size=3)
        assert len(result.interviewers) == 3

    def test_panel_size_equal_to_minimum(self, service, diverse_pool):
        """Panel of exactly min_panel_size (3) is valid."""
        result = service.assign(diverse_pool, panel_size=3)
        assert len(result.interviewers) == 3

    def test_larger_panel_from_large_pool(self, service):
        """Panel size of 4 from a pool of 6 should work."""
        large_pool = [
            Interviewer(id=f"i{i}", name=f"Person {i}",
                       gender="male" if i % 2 == 0 else "female",
                       department=dept)
            for i, dept in enumerate(
                ["engineering", "product", "hr", "design", "legal", "finance"], 1
            )
        ]
        result = service.assign(large_pool, panel_size=4)
        assert len(result.interviewers) == 4


class TestAdditionalNegative:
    def test_gender_diverse_but_same_department_is_rejected(self, service):
        """Gender diversity alone is not enough — departments must also differ."""
        pool = [
            Interviewer(id="i1", name="Alex", gender="male", department="engineering"),
            Interviewer(id="i2", name="Sara", gender="female", department="engineering"),
            Interviewer(id="i3", name="Tom", gender="male", department="engineering"),
        ]
        result = service.assign(pool, panel_size=3)
        assert result.approved is False
        assert "department" in result.rejection_reason.lower()

    def test_department_diverse_but_same_gender_is_rejected(self, service):
        """Department diversity alone is not enough — genders must also differ."""
        pool = [
            Interviewer(id="i1", name="Alex", gender="male", department="engineering"),
            Interviewer(id="i2", name="Tom", gender="male", department="product"),
            Interviewer(id="i3", name="John", gender="male", department="hr"),
        ]
        result = service.assign(pool, panel_size=3)
        assert result.approved is False
        assert "gender" in result.rejection_reason.lower()

    def test_rejection_reason_specifies_which_diversity_failed(self, service):
        """Rejection reason must be specific — not a generic message."""
        pool = [
            Interviewer(id="i1", name="Alex", gender="male", department="engineering"),
            Interviewer(id="i2", name="Tom", gender="male", department="product"),
            Interviewer(id="i3", name="John", gender="male", department="hr"),
        ]
        result = service.assign(pool, panel_size=3)
        assert result.rejection_reason is not None
        assert len(result.rejection_reason) > 20  # not just "failed"

    def test_approved_panel_has_no_rejection_reason(self, service, diverse_pool):
        """Approved panels must have rejection_reason as None, not empty string."""
        result = service.assign(diverse_pool, panel_size=3)
        assert result.rejection_reason is None

    def test_panel_size_of_one_raises(self, service, diverse_pool):
        """Panel of 1 is meaningless for bias mitigation purposes."""
        with pytest.raises(ValueError, match="minimum"):
            service.assign(diverse_pool, panel_size=1)

    def test_pool_with_exactly_one_interviewer_raises(self, service):
        single = [Interviewer(id="i1", name="Alex", gender="male", department="eng")]
        with pytest.raises(ValueError, match="pool"):
            service.assign(single, panel_size=3)


class TestMandatoryInterviewers:
    # ── mandatory people always appear in the result ──────────────────────────

    def test_mandatory_interviewer_is_included(self, service, diverse_pool):
        result = service.assign(diverse_pool, panel_size=3, mandatory_ids=["i1"])
        ids = [iv.id for iv in result.interviewers]
        assert "i1" in ids

    def test_multiple_mandatory_interviewers_all_included(self, service, diverse_pool):
        result = service.assign(diverse_pool, panel_size=3, mandatory_ids=["i1", "i2"])
        ids = [iv.id for iv in result.interviewers]
        assert "i1" in ids
        assert "i2" in ids

    def test_panel_size_still_respected_with_mandatory(self, service, diverse_pool):
        result = service.assign(diverse_pool, panel_size=3, mandatory_ids=["i1"])
        assert len(result.interviewers) == 3

    def test_mandatory_fills_entire_panel_when_count_equals_size(self, service, diverse_pool):
        result = service.assign(diverse_pool, panel_size=3, mandatory_ids=["i1", "i2", "i3"])
        assert len(result.interviewers) == 3
        ids = [iv.id for iv in result.interviewers]
        assert set(ids) == {"i1", "i2", "i3"}

    # ── diversity maximised in remaining slots ────────────────────────────────

    def test_fill_slots_prefer_new_gender(self, service):
        """One mandatory male — remaining slot should prefer a female."""
        pool = [
            Interviewer(id="m1", name="Mandatory", gender="male", department="engineering"),
            Interviewer(id="f1", name="Female opt", gender="female", department="product"),
            Interviewer(id="m2", name="Male opt", gender="male", department="hr"),
        ]
        result = service.assign(pool, panel_size=3, mandatory_ids=["m1"])
        ids = [iv.id for iv in result.interviewers]
        assert "f1" in ids  # female picked to add gender diversity

    def test_diversity_checked_on_full_panel_including_mandatory(self, service):
        """Mandatory members count towards the diversity check."""
        pool = [
            Interviewer(id="i1", name="John", gender="male", department="engineering"),
            Interviewer(id="i2", name="Sara", gender="female", department="engineering"),
            Interviewer(id="i3", name="Tom", gender="male", department="engineering"),
        ]
        # All same department — panel should be rejected even though mandatory is set
        result = service.assign(pool, panel_size=3, mandatory_ids=["i1"])
        assert result.approved is False
        assert "department" in result.rejection_reason.lower()

    # ── validation errors ─────────────────────────────────────────────────────

    def test_mandatory_id_not_in_pool_raises(self, service, diverse_pool):
        with pytest.raises(ValueError, match="not found in pool"):
            service.assign(diverse_pool, panel_size=3, mandatory_ids=["does-not-exist"])

    def test_more_mandatory_than_panel_size_raises(self, service, diverse_pool):
        with pytest.raises(ValueError, match="exceed panel_size"):
            service.assign(diverse_pool, panel_size=3, mandatory_ids=["i1", "i2", "i3", "i4"])

    def test_no_mandatory_ids_behaves_as_before(self, service, diverse_pool):
        """Omitting mandatory_ids is identical to passing an empty list."""
        result_none = service.assign(diverse_pool, panel_size=3)
        result_empty = service.assign(diverse_pool, panel_size=3, mandatory_ids=[])
        assert len(result_none.interviewers) == len(result_empty.interviewers) == 3
