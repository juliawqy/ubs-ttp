"""
Implicit Association Test (IAT) service.

Sessions are mutable aggregates: an employee starts one, submits responses
over time, then completes it. Completion produces an IATResult, which is
private to the employee who took the test -- get_result enforces that no
one else (manager, HR, etc.) can read it. This mirrors the promise shown on
the Training page: results are never shared with HR or used in a performance
review.
"""
from dataclasses import dataclass, field
from shared.base.service import BaseService

VALID_POLES = frozenset({"a", "b"})


@dataclass
class IATResponse:
    category: str
    selected_pole: str
    response_time_ms: float


@dataclass
class IATSession:
    id: int
    employee_id: str
    status: str = "in_progress"  # in_progress | completed
    responses: list[IATResponse] = field(default_factory=list)


@dataclass
class IATResult:
    session_id: int
    employee_id: str
    category_scores: dict[str, float]


class IATService(BaseService):
    """Starts IAT sessions, records responses, and scores completed ones."""

    def start_session(self, session_id: int, employee_id: str) -> IATSession:
        """
        Raises:
            ValueError: employee_id is empty
        """
        if not employee_id.strip():
            raise ValueError("employee_id cannot be empty")
        return IATSession(id=session_id, employee_id=employee_id)

    def submit_response(
        self, session: IATSession, category: str, selected_pole: str, response_time_ms: float
    ) -> IATSession:
        """
        Raises:
            ValueError: session already completed, category empty,
                        selected_pole not "a"/"b", or response_time_ms <= 0
        """
        if session.status == "completed":
            raise ValueError("cannot submit a response to a completed session")
        if not category.strip():
            raise ValueError("category cannot be empty")
        if selected_pole not in VALID_POLES:
            raise ValueError(f"selected_pole must be one of {sorted(VALID_POLES)}")
        if response_time_ms <= 0:
            raise ValueError("response_time_ms must be positive")

        session.responses.append(
            IATResponse(category=category, selected_pole=selected_pole, response_time_ms=response_time_ms)
        )
        return session

    def complete_session(self, session: IATSession) -> IATResult:
        """
        Raises:
            ValueError: session already completed, or has no responses
        """
        if session.status == "completed":
            raise ValueError("session is already completed")
        if not session.responses:
            raise ValueError("cannot complete a session with no responses")

        session.status = "completed"
        return IATResult(
            session_id=session.id,
            employee_id=session.employee_id,
            category_scores=self._score(session.responses),
        )

    def get_result(self, result: IATResult, requesting_employee_id: str) -> IATResult:
        """
        Raises:
            PermissionError: requesting_employee_id did not take this test
        """
        if requesting_employee_id != result.employee_id:
            raise PermissionError("IAT results are private to the employee who took the test")
        return result

    # -- internals ------------------------------------------------------------

    def _score(self, responses: list[IATResponse]) -> dict[str, float]:
        """
        Heuristic only, not a clinically validated D-score: per category,
        the average response time for pole "b" minus pole "a". A positive
        value means pole "a" answers were faster on average.
        """
        by_category: dict[str, list[IATResponse]] = {}
        for response in responses:
            by_category.setdefault(response.category, []).append(response)

        scores = {}
        for category, items in by_category.items():
            a_times = [r.response_time_ms for r in items if r.selected_pole == "a"]
            b_times = [r.response_time_ms for r in items if r.selected_pole == "b"]
            avg_a = sum(a_times) / len(a_times) if a_times else 0.0
            avg_b = sum(b_times) / len(b_times) if b_times else 0.0
            scores[category] = avg_b - avg_a
        return scores
