"""
Unit tests for IATService.
Run: pytest services/training/tests/unit/test_iat_service.py -v
"""
import pytest
from app.services.iat import IATService, IATSession, IATResult


@pytest.fixture
def service():
    return IATService()


class TestStartSession:
    def test_returns_iat_session_type(self, service):
        session = service.start_session(1, "emp-1")
        assert isinstance(session, IATSession)

    def test_status_is_in_progress(self, service):
        session = service.start_session(1, "emp-1")
        assert session.status == "in_progress"

    def test_responses_start_empty(self, service):
        session = service.start_session(1, "emp-1")
        assert session.responses == []

    def test_preserves_employee_id(self, service):
        session = service.start_session(1, "emp-1")
        assert session.employee_id == "emp-1"

    def test_empty_employee_id_raises(self, service):
        with pytest.raises(ValueError, match="employee_id"):
            service.start_session(1, "")


class TestSubmitResponse:
    def test_appends_response(self, service):
        session = service.start_session(1, "emp-1")
        service.submit_response(session, "gender-leadership", "a", 850)
        assert len(session.responses) == 1

    def test_multiple_responses_accumulate(self, service):
        session = service.start_session(1, "emp-1")
        service.submit_response(session, "gender-leadership", "a", 850)
        service.submit_response(session, "gender-leadership", "b", 900)
        assert len(session.responses) == 2

    def test_invalid_pole_raises(self, service):
        session = service.start_session(1, "emp-1")
        with pytest.raises(ValueError, match="selected_pole"):
            service.submit_response(session, "gender-leadership", "c", 850)

    def test_non_positive_response_time_raises(self, service):
        session = service.start_session(1, "emp-1")
        with pytest.raises(ValueError, match="response_time_ms"):
            service.submit_response(session, "gender-leadership", "a", 0)

    def test_empty_category_raises(self, service):
        session = service.start_session(1, "emp-1")
        with pytest.raises(ValueError, match="category"):
            service.submit_response(session, "", "a", 850)

    def test_cannot_submit_after_completion(self, service):
        session = service.start_session(1, "emp-1")
        service.submit_response(session, "gender-leadership", "a", 850)
        service.complete_session(session)
        with pytest.raises(ValueError, match="completed"):
            service.submit_response(session, "gender-leadership", "b", 900)


class TestCompleteSession:
    def test_returns_iat_result_type(self, service):
        session = service.start_session(1, "emp-1")
        service.submit_response(session, "gender-leadership", "a", 850)
        result = service.complete_session(session)
        assert isinstance(result, IATResult)

    def test_marks_session_completed(self, service):
        session = service.start_session(1, "emp-1")
        service.submit_response(session, "gender-leadership", "a", 850)
        service.complete_session(session)
        assert session.status == "completed"

    def test_empty_session_raises(self, service):
        session = service.start_session(1, "emp-1")
        with pytest.raises(ValueError, match="no responses"):
            service.complete_session(session)

    def test_cannot_complete_twice(self, service):
        session = service.start_session(1, "emp-1")
        service.submit_response(session, "gender-leadership", "a", 850)
        service.complete_session(session)
        with pytest.raises(ValueError, match="already completed"):
            service.complete_session(session)

    def test_category_scores_keyed_by_category(self, service):
        session = service.start_session(1, "emp-1")
        service.submit_response(session, "gender-leadership", "a", 850)
        service.submit_response(session, "age-tech", "b", 700)
        result = service.complete_session(session)
        assert set(result.category_scores.keys()) == {"gender-leadership", "age-tech"}


class TestScoring:
    def test_score_reflects_response_time_difference(self, service):
        session = service.start_session(1, "emp-1")
        service.submit_response(session, "cat", "a", 600)
        service.submit_response(session, "cat", "b", 900)
        result = service.complete_session(session)
        assert result.category_scores["cat"] == pytest.approx(300)

    def test_single_pole_category_does_not_crash(self, service):
        session = service.start_session(1, "emp-1")
        service.submit_response(session, "cat", "a", 600)
        result = service.complete_session(session)
        assert result.category_scores["cat"] == pytest.approx(-600)


class TestPrivacy:
    def test_owner_can_access_own_result(self, service):
        session = service.start_session(1, "emp-1")
        service.submit_response(session, "cat", "a", 600)
        result = service.complete_session(session)
        assert service.get_result(result, "emp-1") is result

    def test_other_employee_cannot_access_result(self, service):
        session = service.start_session(1, "emp-1")
        service.submit_response(session, "cat", "a", 600)
        result = service.complete_session(session)
        with pytest.raises(PermissionError):
            service.get_result(result, "emp-2")

    def test_result_employee_id_matches_session(self, service):
        session = service.start_session(1, "emp-1")
        service.submit_response(session, "cat", "a", 600)
        result = service.complete_session(session)
        assert result.employee_id == "emp-1"
