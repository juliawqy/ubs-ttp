"""
Unit tests for FeedbackService.
Run: pytest services/performance/tests/unit/test_feedback_service.py -v
"""
import pytest
from app.services.feedback import FeedbackService
from app.models import FeedbackEntry, AnonymisedFeedback


@pytest.fixture
def service():
    return FeedbackService()


class TestSubmit:
    def test_returns_feedback_entry_instance(self, service):
        result = service.submit("emp-1", "rater-1", "Great collaborator on cross-team projects.")
        assert isinstance(result, FeedbackEntry)

    def test_preserves_employee_id(self, service):
        result = service.submit("emp-1", "rater-1", "Great collaborator.")
        assert result.employee_id == "emp-1"

    def test_preserves_rater_id_internally(self, service):
        # rater_id is retained on the raw entry -- it just must never leak
        # into the aggregated view (covered in TestAggregation below).
        result = service.submit("emp-1", "rater-1", "Great collaborator.")
        assert result.rater_id == "rater-1"

    def test_preserves_comments(self, service):
        result = service.submit("emp-1", "rater-1", "Great collaborator.")
        assert result.comments == "Great collaborator."

    def test_same_employee_can_receive_feedback_from_multiple_raters(self, service):
        service.submit("emp-1", "rater-1", "Strong technical contributor.")
        service.submit("emp-1", "rater-2", "Could improve on deadlines.")
        aggregated = service.get_aggregated("emp-1")
        assert aggregated.count == 2

    def test_same_rater_can_submit_feedback_for_different_employees(self, service):
        service.submit("emp-1", "rater-1", "Solid performer.")
        service.submit("emp-2", "rater-1", "Needs more initiative.")
        assert service.get_aggregated("emp-1").count == 1
        assert service.get_aggregated("emp-2").count == 1


class TestValidation:
    def test_empty_employee_id_raises(self, service):
        with pytest.raises(ValueError, match="employee_id"):
            service.submit("", "rater-1", "Some feedback.")

    def test_whitespace_only_employee_id_raises(self, service):
        with pytest.raises(ValueError, match="employee_id"):
            service.submit("   ", "rater-1", "Some feedback.")

    def test_empty_rater_id_raises(self, service):
        with pytest.raises(ValueError, match="rater_id"):
            service.submit("emp-1", "", "Some feedback.")

    def test_whitespace_only_rater_id_raises(self, service):
        with pytest.raises(ValueError, match="rater_id"):
            service.submit("emp-1", "   ", "Some feedback.")

    def test_empty_comments_raises(self, service):
        with pytest.raises(ValueError, match="comments"):
            service.submit("emp-1", "rater-1", "")

    def test_whitespace_only_comments_raises(self, service):
        with pytest.raises(ValueError, match="comments"):
            service.submit("emp-1", "rater-1", "   ")


class TestDuplicateSubmissionBlocked:
    def test_same_rater_cannot_submit_twice_for_same_employee(self, service):
        service.submit("emp-1", "rater-1", "First piece of feedback.")
        with pytest.raises(ValueError, match="already submitted"):
            service.submit("emp-1", "rater-1", "Trying again.")

    def test_duplicate_attempt_does_not_change_aggregated_count(self, service):
        service.submit("emp-1", "rater-1", "First piece of feedback.")
        try:
            service.submit("emp-1", "rater-1", "Trying again.")
        except ValueError:
            pass
        assert service.get_aggregated("emp-1").count == 1


class TestAggregation:
    def test_returns_anonymised_feedback_instance(self, service):
        service.submit("emp-1", "rater-1", "Great mentor.")
        result = service.get_aggregated("emp-1")
        assert isinstance(result, AnonymisedFeedback)

    def test_aggregated_view_never_exposes_rater_id(self, service):
        service.submit("emp-1", "rater-1", "Great mentor.")
        result = service.get_aggregated("emp-1")
        assert "rater_id" not in vars(result)
        assert "rater-1" not in result.comments

    def test_aggregated_view_includes_all_comments(self, service):
        service.submit("emp-1", "rater-1", "Strong technical contributor.")
        service.submit("emp-1", "rater-2", "Could improve on deadlines.")
        result = service.get_aggregated("emp-1")
        assert set(result.comments) == {"Strong technical contributor.", "Could improve on deadlines."}

    def test_aggregated_view_for_employee_with_no_feedback_is_empty(self, service):
        result = service.get_aggregated("emp-unknown")
        assert result.count == 0
        assert result.comments == []

    def test_aggregated_view_only_includes_feedback_for_requested_employee(self, service):
        service.submit("emp-1", "rater-1", "Feedback for emp 1.")
        service.submit("emp-2", "rater-1", "Feedback for emp 2.")
        result = service.get_aggregated("emp-1")
        assert result.comments == ["Feedback for emp 1."]
