"""
Job postings service -- handles manager requests to open a new role.

A job posting starts as a request from a hiring manager to the hiring
department. The manager describes what they need; the hiring department
reviews and publishes. Bias check on the description is advisory --
flags are surfaced to the manager so they can revise before submission.
"""
from dataclasses import dataclass, field
from shared.base.service import BaseService
from shared.bias_analyzer.bias_analyzer import BiasAnalyzer
from shared.bias_analyzer.models import BiasAnalysisResult


@dataclass
class HiringManager:
    id: str
    name: str
    department: str
    email: str


@dataclass
class JobPostingRequest:
    title: str
    description: str
    requirements: list[str]
    department: str       # department the role sits in
    manager: HiringManager


@dataclass
class JobPostingResult:
    title: str
    description: str
    requirements: list[str]
    department: str
    manager: HiringManager
    status: str                  # "pending" until hiring dept reviews
    bias_check: BiasAnalysisResult


class JobPostingsService(BaseService):
    """
    Validates and processes a manager's request to open a new role.
    Returns the request with a bias check result so the manager can
    revise before the posting goes to the hiring department.
    """

    def __init__(self, bias_analyzer: BiasAnalyzer | None = None):
        # Injected for testability; defaults to rule-based (no AI cost)
        self._bias_analyzer = bias_analyzer or BiasAnalyzer()

    def create_request(self, request: JobPostingRequest) -> JobPostingResult:
        """
        Validate the request and run a bias check on the description.

        Raises:
            ValueError: if title, description, or requirements are missing
        """
        self._validate(request)

        bias_result = self._bias_analyzer.analyse(request.description)

        return JobPostingResult(
            title=request.title,
            description=request.description,
            requirements=request.requirements,
            department=request.department,
            manager=request.manager,
            status="pending",
            bias_check=bias_result,
        )

    # -- internals ------------------------------------------------------------

    def _validate(self, request: JobPostingRequest) -> None:
        if not request.title.strip():
            raise ValueError("title cannot be empty")
        if not request.description.strip():
            raise ValueError("description cannot be empty")
        if not request.requirements:
            raise ValueError("at least one requirement must be listed")
        if not request.manager.id.strip():
            raise ValueError("manager id cannot be empty")
        if not request.manager.email.strip():
            raise ValueError("manager email cannot be empty")
