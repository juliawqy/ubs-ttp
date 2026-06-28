"""
Career path mapping service -- tracks an employee's current role, next
milestone, and the skills recommended to bridge the two.
"""
from dataclasses import dataclass, field
from datetime import date
from shared.base.service import BaseService
from app.services.recommendation_engine import RecommendationEngine


@dataclass
class CareerPathRequest:
    employee_name: str
    current_role: str
    next_milestone: str
    target_date: date


@dataclass
class CareerPathResult:
    employee_name: str
    current_role: str
    next_milestone: str
    target_date: date
    recommended_skills: list[str] = field(default_factory=list)


class CareerPathService(BaseService):
    """
    DIP: depends on RecommendationEngine through its constructor so the
    recommendation strategy (rule-based today, AI-assisted later) can be
    swapped without changing this class.
    """

    def __init__(self, recommendation_engine: RecommendationEngine | None = None):
        self._recommendation_engine = recommendation_engine or RecommendationEngine()

    def create_entry(self, request: CareerPathRequest) -> CareerPathResult:
        """
        Validate the request and attach recommended skills for the gap
        between current_role and next_milestone. Used for both create and
        update -- persistence and identity live in the router.

        Raises:
            ValueError: if employee_name, current_role, next_milestone, or
                        target_date is missing
        """
        self._validate(request)
        skills = self._recommendation_engine.recommend(request.current_role, request.next_milestone)

        return CareerPathResult(
            employee_name=request.employee_name,
            current_role=request.current_role,
            next_milestone=request.next_milestone,
            target_date=request.target_date,
            recommended_skills=skills,
        )

    # -- internals ------------------------------------------------------------

    def _validate(self, request: CareerPathRequest) -> None:
        if not request.employee_name.strip():
            raise ValueError("employee_name cannot be empty")
        if not request.current_role.strip():
            raise ValueError("current_role cannot be empty")
        if not request.next_milestone.strip():
            raise ValueError("next_milestone cannot be empty")
        if request.target_date is None:
            raise ValueError("target_date is required")
