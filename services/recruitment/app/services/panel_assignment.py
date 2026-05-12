"""
Panel assignment service — assigns diverse interview panels.
Rejects panels that lack gender or department diversity.
Bias mitigation: prevents homogeneous groups from making hiring decisions unchallenged.
"""
from dataclasses import dataclass, field
from shared.base.service import BaseService


@dataclass
class Interviewer:
    id: str
    name: str
    gender: str
    department: str


@dataclass
class PanelAssignment:
    interviewers: list[Interviewer]
    approved: bool
    rejection_reason: str | None = None


class PanelAssignmentService(BaseService):
    """
    Selects a diverse interview panel from a pool of interviewers.
    A panel is approved only if it has both gender and department diversity.
    """

    def __init__(self, min_panel_size: int = 3):
        self._min_panel_size = min_panel_size

    def assign(
        self,
        interviewer_pool: list[Interviewer],
        panel_size: int,
    ) -> PanelAssignment:
        """
        Select a panel of panel_size from the pool and check diversity.

        Args:
            interviewer_pool: all available interviewers to choose from
            panel_size: how many interviewers to select

        Returns:
            PanelAssignment with approved=True if diverse, False with reason if not

        Raises:
            ValueError: if pool is empty, too small, or panel_size below minimum
        """
        self._validate_inputs(interviewer_pool, panel_size)

        panel = self._select_diverse_panel(interviewer_pool, panel_size)
        rejection_reason = self._check_diversity(panel)

        return PanelAssignment(
            interviewers=panel,
            approved=rejection_reason is None,
            rejection_reason=rejection_reason,
        )

    def _validate_inputs(
        self,
        pool: list[Interviewer],
        panel_size: int,
    ) -> None:
        if not pool:
            raise ValueError("interviewer pool cannot be empty")

        if panel_size < self._min_panel_size:
            raise ValueError(
                f"panel size {panel_size} is below minimum of {self._min_panel_size}"
            )

        if len(pool) < panel_size:
            raise ValueError(
                f"pool has {len(pool)} interviewers but panel_size is {panel_size} — "
                "pool must be at least as large as the requested panel"
            )

    def _select_diverse_panel(
        self,
        pool: list[Interviewer],
        panel_size: int,
    ) -> list[Interviewer]:
        """
        Greedily select interviewers prioritising gender and department diversity.
        Picks one from each unique gender first, then fills remaining slots
        prioritising departments not yet represented.
        """
        selected = []
        seen_genders: set[str] = set()
        seen_depts: set[str] = set()

        # First pass: one per gender
        for interviewer in pool:
            if len(selected) >= panel_size:
                break
            if interviewer.gender not in seen_genders:
                selected.append(interviewer)
                seen_genders.add(interviewer.gender)
                seen_depts.add(interviewer.department)

        # Second pass: fill remaining slots with new departments
        for interviewer in pool:
            if len(selected) >= panel_size:
                break
            if interviewer not in selected and interviewer.department not in seen_depts:
                selected.append(interviewer)
                seen_depts.add(interviewer.department)

        # Third pass: fill any remaining slots
        for interviewer in pool:
            if len(selected) >= panel_size:
                break
            if interviewer not in selected:
                selected.append(interviewer)

        return selected[:panel_size]

    def _check_diversity(self, panel: list[Interviewer]) -> str | None:
        """
        Returns a rejection reason string if the panel fails diversity checks,
        or None if the panel is approved.
        """
        genders = {i.gender for i in panel}
        departments = {i.department for i in panel}

        if len(genders) < 2:
            return (
                f"Panel lacks gender diversity — all members identify as '{next(iter(genders))}'. "
                "At least two genders must be represented."
            )

        if len(departments) < 2:
            return (
                f"Panel lacks department diversity — all members are from '{next(iter(departments))}'. "
                "At least two departments must be represented."
            )

        return None
