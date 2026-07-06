"""
Feedback service -- stores multi-rater 360 feedback and returns a fully
anonymised aggregated view.

Unlike PerformanceScoringService/ReviewService (stateless: each call is
validated independently), this service deliberately owns persistence
itself rather than leaving it to a router-level *Store class. The
one-submission-per-rater-per-employee rule is a genuine domain invariant
that requires seeing the full submission history to enforce, so storage
and that invariant are kept together here rather than split across layers.

rater_id is retained in the raw store purely to enforce that invariant.
It is never copied onto AnonymisedFeedback -- the aggregated view has no
rater_id field at all, so there is nothing to accidentally expose later.
"""
import re
from shared.base.service import BaseService
from app.models import AnonymisedFeedback, FeedbackEntry

_OFFENSIVE_RE = re.compile(
    r"\b(idiot|moron|stupid(?:\s+\w+)?|useless|waste of space|incompetent fool"
    r"|dumb(?:\s+\w+)?|loser|jerk|asshole|bastard|bitch|pathetic|worthless)\b",
    re.IGNORECASE,
)


class FeedbackService(BaseService):
    """In-memory 360 feedback store with anonymised aggregation."""

    def __init__(self):
        self._entries: list[FeedbackEntry] = []

    def submit(self, employee_id: str, rater_id: str, comments: str) -> FeedbackEntry:
        """
        Validate and record one rater's feedback about an employee.

        Raises:
            ValueError: if employee_id/rater_id/comments is empty, if this
                        rater has already submitted for this employee, or if
                        comments contain clearly offensive language.
        """
        self._validate(employee_id, rater_id, comments)

        if self._has_already_submitted(employee_id, rater_id):
            raise ValueError(
                f"rater '{rater_id}' has already submitted feedback for employee '{employee_id}'"
            )

        entry = FeedbackEntry(employee_id=employee_id, rater_id=rater_id, comments=comments)
        self._entries.append(entry)
        return entry

    def get_aggregated(self, employee_id: str) -> AnonymisedFeedback:
        """Returns every comment submitted for an employee, with rater identity stripped."""
        matching = [e for e in self._entries if e.employee_id == employee_id]
        return AnonymisedFeedback(
            employee_id=employee_id,
            comments=[e.comments for e in matching],
            count=len(matching),
        )

    # -- internals ------------------------------------------------------------

    def _has_already_submitted(self, employee_id: str, rater_id: str) -> bool:
        return any(
            e.employee_id == employee_id and e.rater_id == rater_id
            for e in self._entries
        )

    def _validate(self, employee_id: str, rater_id: str, comments: str) -> None:
        if not employee_id or not employee_id.strip():
            raise ValueError("employee_id cannot be empty")
        if not rater_id or not rater_id.strip():
            raise ValueError("rater_id cannot be empty")
        if not comments or not comments.strip():
            raise ValueError("comments cannot be empty")
        if _OFFENSIVE_RE.search(comments):
            raise ValueError(
                "Comments contain offensive or harassing language. "
                "Please use professional, behaviour-focused language."
            )
