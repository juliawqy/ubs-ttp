"""
Recommendation engine -- suggests skills an employee should build to move
from their current role toward their next career milestone.

Rule-based for now (deterministic, no AI cost). A future AI-assisted
version can be swapped in behind the same `recommend` interface without
touching CareerPathService, which depends only on this class.
"""
from shared.base.service import BaseService

DEFAULT_SKILLS = ["Communication", "Leadership Fundamentals"]

_ROLE_SKILL_MAP: dict[tuple[str, str], list[str]] = {
    ("software engineer", "senior software engineer"):
        ["System Design", "Code Review", "Mentoring"],
    ("senior software engineer", "engineering manager"):
        ["People Management", "Performance Reviews", "Budgeting"],
    ("analyst", "senior analyst"):
        ["Advanced Excel", "Data Storytelling", "Stakeholder Management"],
    ("sales associate", "account manager"):
        ["Negotiation", "Client Relationship Management"],
}


class RecommendationEngine(BaseService):
    """Maps (current_role, next_milestone) to a list of recommended skills."""

    def recommend(self, current_role: str, next_milestone: str) -> list[str]:
        """
        Raises:
            ValueError: if current_role or next_milestone is empty
        """
        if not current_role.strip():
            raise ValueError("current_role cannot be empty")
        if not next_milestone.strip():
            raise ValueError("next_milestone cannot be empty")

        key = (current_role.strip().lower(), next_milestone.strip().lower())
        return list(_ROLE_SKILL_MAP.get(key, DEFAULT_SKILLS))
