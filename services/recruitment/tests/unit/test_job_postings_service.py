"""
Unit tests for JobPostingsService.
Run: pytest services/recruitment/tests/unit/test_job_postings_service.py -v
"""
import pytest
from app.services.job_postings import (
    JobPostingsService,
    JobPostingRequest,
    JobPostingResult,
    HiringManager,
)


@pytest.fixture
def service():
    return JobPostingsService()


@pytest.fixture
def manager():
    return HiringManager(
        id="mgr-001",
        name="Julia Wong",
        department="Engineering",
        email="julia.wong@ubs.com",
    )


@pytest.fixture
def valid_request(manager):
    return JobPostingRequest(
        title="Senior Python Engineer",
        description="We are looking for an experienced engineer to build scalable APIs.",
        requirements=["Python", "SQL", "REST APIs"],
        department="Engineering",
        manager=manager,
    )


class TestCreateRequest:
    def test_returns_job_posting_result(self, service, valid_request):
        result = service.create_request(valid_request)
        assert isinstance(result, JobPostingResult)

    def test_status_is_pending(self, service, valid_request):
        result = service.create_request(valid_request)
        assert result.status == "pending"

    def test_preserves_title_and_description(self, service, valid_request):
        result = service.create_request(valid_request)
        assert result.title == valid_request.title
        assert result.description == valid_request.description

    def test_preserves_requirements(self, service, valid_request):
        result = service.create_request(valid_request)
        assert result.requirements == valid_request.requirements

    def test_preserves_manager_details(self, service, valid_request, manager):
        result = service.create_request(valid_request)
        assert result.manager.id == manager.id
        assert result.manager.name == manager.name
        assert result.manager.department == manager.department
        assert result.manager.email == manager.email


class TestBiasCheck:
    def test_clean_description_is_not_flagged(self, service, valid_request):
        result = service.create_request(valid_request)
        assert result.bias_check.flagged is False
        assert result.bias_check.flagged_phrases == []

    def test_biased_description_is_flagged(self, service, valid_request):
        valid_request.description = "We need a rockstar ninja who is a culture fit."
        result = service.create_request(valid_request)
        assert result.bias_check.flagged is True

    def test_bias_check_includes_flagged_phrases(self, service, valid_request):
        valid_request.description = "Looking for a rockstar developer."
        result = service.create_request(valid_request)
        phrases = [fp.phrase for fp in result.bias_check.flagged_phrases]
        assert "rockstar" in phrases

    def test_bias_check_does_not_block_submission(self, service, valid_request):
        """Biased postings still go through — manager is informed, not blocked."""
        valid_request.description = "We need a rockstar ninja."
        result = service.create_request(valid_request)
        assert result.status == "pending"

    def test_bias_check_phrase_includes_suggestion(self, service, valid_request):
        valid_request.description = "Must be a digital native."
        result = service.create_request(valid_request)
        assert len(result.bias_check.flagged_phrases) > 0
        assert result.bias_check.flagged_phrases[0].suggestion != ""


class TestValidation:
    def test_empty_title_raises(self, service, valid_request):
        valid_request.title = ""
        with pytest.raises(ValueError, match="title"):
            service.create_request(valid_request)

    def test_whitespace_title_raises(self, service, valid_request):
        valid_request.title = "   "
        with pytest.raises(ValueError, match="title"):
            service.create_request(valid_request)

    def test_empty_description_raises(self, service, valid_request):
        valid_request.description = ""
        with pytest.raises(ValueError, match="description"):
            service.create_request(valid_request)

    def test_empty_requirements_raises(self, service, valid_request):
        valid_request.requirements = []
        with pytest.raises(ValueError, match="requirement"):
            service.create_request(valid_request)

    def test_empty_manager_id_raises(self, service, valid_request):
        valid_request.manager.id = ""
        with pytest.raises(ValueError, match="manager id"):
            service.create_request(valid_request)

    def test_empty_manager_email_raises(self, service, valid_request):
        valid_request.manager.email = ""
        with pytest.raises(ValueError, match="manager email"):
            service.create_request(valid_request)
