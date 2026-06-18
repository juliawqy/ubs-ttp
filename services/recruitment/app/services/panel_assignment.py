"""
Panel assignment service -- assigns diverse interview panels.
Rejects panels that lack gender or department diversity.
Bias mitigation: prevents homogeneous groups from making hiring decisions unchallenged.
"""
from dataclasses import dataclass
from shared.base.service import BaseService


@dataclass
class Interviewer:
    id: str
    name: str
    gender: str
    department: str
    seniority: str = ""


@dataclass
class PanelAssignment:
    interviewers: list[Interviewer]
    approved: bool
    rejection_reason: str | None = None


MIN_PANEL_SIZE = 3
MIN_GENDER_COUNT = 2
MIN_DEPT_COUNT = 2


class PanelAssignmentService(BaseService):
    """
    Selects a diverse interview panel from a pool of interviewers.

    Supports mandatory members: specific interviewers who must be on the panel
    (e.g. hiring manager, subject-matter expert). Remaining slots are filled
    from the pool to maximise gender and department diversity.

    Diversity is checked on the full panel including mandatory members --
    the result is a suggestion; the final decision is always human-in-the-loop.

    OCP: min_gender_count and min_dept_count are injectable so diversity
    requirements can change without modifying this class.
    """

    def __init__(
        self,
        min_panel_size: int = MIN_PANEL_SIZE,
        min_gender_count: int = MIN_GENDER_COUNT,
        min_dept_count: int = MIN_DEPT_COUNT,
    ):
        self._min_panel_size = min_panel_size
        self._min_gender_count = min_gender_count
        self._min_dept_count = min_dept_count

    def assign(
        self,
        interviewer_pool: list[Interviewer],
        panel_size: int,
        mandatory_ids: list[str] | None = None,
    ) -> PanelAssignment:
        """
        Select a panel of panel_size from the pool and check diversity.

        Args:
            interviewer_pool: all available interviewers to choose from
            panel_size: total number of interviewers on the panel
            mandatory_ids: IDs of interviewers who must be included;
                           they must all exist in interviewer_pool

        Returns:
            PanelAssignment with approved=True if diverse, False with reason if not

        Raises:
            ValueError: pool empty/too small, panel_size below minimum,
                        mandatory ID not found, or more mandatory than panel_size
        """
        mandatory_ids = mandatory_ids or []

        pool_by_id = {iv.id: iv for iv in interviewer_pool}
        mandatory = self._resolve_mandatory(mandatory_ids, pool_by_id)

        self._validate_inputs(interviewer_pool, panel_size, mandatory)

        remaining_slots = panel_size - len(mandatory)
        optional_pool = [iv for iv in interviewer_pool if iv.id not in {m.id for m in mandatory}]

        filled = self._select_diverse_panel(
            pool=optional_pool,
            slots=remaining_slots,
            seed_genders={m.gender for m in mandatory},
            seed_depts={m.department for m in mandatory},
        )

        panel = mandatory + filled
        rejection_reason = self._check_diversity(panel)

        return PanelAssignment(
            interviewers=panel,
            approved=rejection_reason is None,
            rejection_reason=rejection_reason,
        )

    # -- internals ------------------------------------------------------------

    def _resolve_mandatory(
        self,
        mandatory_ids: list[str],
        pool_by_id: dict[str, Interviewer],
    ) -> list[Interviewer]:
        missing = [mid for mid in mandatory_ids if mid not in pool_by_id]
        if missing:
            raise ValueError(
                f"mandatory interviewer(s) not found in pool: {', '.join(missing)}"
            )
        return [pool_by_id[mid] for mid in mandatory_ids]

    def _validate_inputs(
        self,
        pool: list[Interviewer],
        panel_size: int,
        mandatory: list[Interviewer],
    ) -> None:
        if not pool:
            raise ValueError("interviewer pool cannot be empty")

        if panel_size < self._min_panel_size:
            raise ValueError(
                f"panel size {panel_size} is below minimum of {self._min_panel_size}"
            )

        if len(mandatory) > panel_size:
            raise ValueError(
                f"{len(mandatory)} mandatory interviewer(s) exceed panel_size of {panel_size}"
            )

        if len(pool) < panel_size:
            raise ValueError(
                f"pool has {len(pool)} interviewers but panel_size is {panel_size} -- "
                "pool must be at least as large as the requested panel"
            )

    def _select_diverse_panel(
        self,
        pool: list[Interviewer],
        slots: int,
        seed_genders: set[str],
        seed_depts: set[str],
    ) -> list[Interviewer]:
        """
        Greedily fill *slots* from pool, maximising diversity given what
        mandatory members already cover (seed_genders / seed_depts).
        """
        selected: list[Interviewer] = []
        seen_genders = set(seed_genders)
        seen_depts = set(seed_depts)

        # First pass: new genders not yet represented
        for iv in pool:
            if len(selected) >= slots:
                break
            if iv.gender not in seen_genders:
                selected.append(iv)
                seen_genders.add(iv.gender)
                seen_depts.add(iv.department)

        # Second pass: new departments not yet represented
        for iv in pool:
            if len(selected) >= slots:
                break
            if iv not in selected and iv.department not in seen_depts:
                selected.append(iv)
                seen_depts.add(iv.department)

        # Third pass: fill any remaining slots
        for iv in pool:
            if len(selected) >= slots:
                break
            if iv not in selected:
                selected.append(iv)

        return selected

    def _check_diversity(self, panel: list[Interviewer]) -> str | None:
        genders = {i.gender for i in panel}
        departments = {i.department for i in panel}

        if len(genders) < self._min_gender_count:
            return (
                f"Panel lacks gender diversity -- all members identify as '{next(iter(genders))}'. "
                f"At least {self._min_gender_count} genders must be represented."
            )

        if len(departments) < self._min_dept_count:
            return (
                f"Panel lacks department diversity -- all members are from '{next(iter(departments))}'. "
                f"At least {self._min_dept_count} departments must be represented."
            )

        return None
