from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import reviews, feedback


def _seed() -> None:
    """Pre-populate the in-memory stores with demo data on startup."""
    from app.routers.reviews import _store
    from app.routers.feedback import _feedback_service
    from app.models import CriterionScore, ScoreBreakdown, Review, FeedbackEntry
    from shared.bias_analyzer.models import BiasAnalysisResult, FlaggedPhrase

    # ── helpers ──────────────────────────────────────────────────────────────
    def _clean() -> BiasAnalysisResult:
        return BiasAnalysisResult(flagged=False, flagged_phrases=[], ai_used=False)

    def _flag(phrase: str, reason: str, suggestion: str) -> BiasAnalysisResult:
        return BiasAnalysisResult(
            flagged=True,
            flagged_phrases=[FlaggedPhrase(phrase=phrase, reason=reason, suggestion=suggestion)],
            ai_used=False,
        )

    def _make_review(
        employee_id: str,
        reviewer_id: str,
        criteria_data: dict[str, tuple[int, str]],
        bias_checks: dict | None = None,
    ) -> None:
        criteria = [
            CriterionScore(criterion=k, score=v[0], comments=v[1])
            for k, v in criteria_data.items()
        ]
        per_criterion = {k: v[0] for k, v in criteria_data.items()}
        average = round(sum(per_criterion.values()) / len(per_criterion), 2)
        review = Review(
            employee_id=employee_id,
            reviewer_id=reviewer_id,
            criteria=criteria,
            score=ScoreBreakdown(per_criterion=per_criterion, average=average),
            bias_checks=bias_checks or {},
        )
        _store.add(review)

    # ── seeded reviews ────────────────────────────────────────────────────────

    # emp-001 — clean, high scorer
    _make_review("emp-001", "mgr-001", {
        "technical_skill": (5, "Consistently delivers high-quality, well-tested code."),
        "communication":   (5, "Clear and concise in written and verbal updates."),
        "collaboration":   (4, "Strong team contributor who unblocks colleagues proactively."),
        "ownership":       (5, "Takes full accountability for deliverables end to end."),
        "growth":          (4, "Rapidly ramped up on two new domains this cycle."),
    })

    # emp-002 — bias flagged: "aggressive"
    _aggressive = _flag(
        phrase="aggressive in meetings",
        reason="'Aggressive' is a gendered term disproportionately applied to women and minorities.",
        suggestion="Describe the specific behaviour: e.g. 'interrupts colleagues before they finish speaking'.",
    )
    _make_review("emp-002", "mgr-001", {
        "technical_skill": (3, "Solid fundamentals but documentation is often incomplete."),
        "communication":   (2, "Tends to be aggressive in meetings; talks over peers."),
        "collaboration":   (3, "Works well one-on-one but can be aggressive in group settings."),
        "ownership":       (4, "Reliably delivers against sprint commitments."),
        "growth":          (3, "Progressing steadily but has not taken on stretch assignments."),
    }, bias_checks={"communication": _aggressive, "collaboration": _aggressive})

    # emp-003 — bias flagged: "culture fit"
    _culture = _flag(
        phrase="doesn't fit our culture",
        reason="'Culture fit' is a subjective criterion that can mask bias against underrepresented groups.",
        suggestion="Specify the observable behaviour: e.g. 'misses stand-ups without notice'.",
    )
    _make_review("emp-003", "mgr-002", {
        "technical_skill": (3, "Adequate technical output this cycle."),
        "communication":   (2, "Doesn't fit our culture and struggles to gel with the team."),
        "collaboration":   (2, "Not a culture fit — often works in isolation."),
        "ownership":       (3, "Meets basic expectations."),
        "growth":          (2, "Limited engagement with development opportunities."),
    }, bias_checks={"communication": _culture, "collaboration": _culture})

    # emp-004 — clean, mid scorer
    _make_review("emp-004", "mgr-002", {
        "technical_skill": (4, "Reliable delivery across all assigned tasks."),
        "communication":   (4, "Communicates blockers early and updates stakeholders regularly."),
        "collaboration":   (4, "Positive team member; frequently volunteers for cross-team work."),
        "ownership":       (3, "Generally accountable but occasionally needs follow-through reminders."),
        "growth":          (4, "Completed leadership training and has started mentoring junior engineers."),
    })

    # ── seeded 360 feedback ───────────────────────────────────────────────────
    _feedback_service._entries.extend([
        FeedbackEntry("emp-001", "emp-002",
            "Excellent communicator. Always explains the reasoning behind decisions, "
            "which helps the whole team align faster."),
        FeedbackEntry("emp-001", "emp-003",
            "Goes out of their way to unblock others. Very reliable pairing partner."),
        FeedbackEntry("emp-002", "emp-001",
            "Technically strong. Could improve on sharing work-in-progress earlier "
            "so we can catch issues sooner."),
        FeedbackEntry("emp-003", "emp-004",
            "Good intentions but async updates can be hard to follow. "
            "More structure in written messages would help the team."),
        FeedbackEntry("emp-004", "emp-001",
            "Proactive about flagging risks before they become problems. "
            "Makes the team feel safe raising concerns."),
    ])


@asynccontextmanager
async def lifespan(app: FastAPI):
    _seed()
    yield


app = FastAPI(title="aequus-performance", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(reviews.router)
app.include_router(feedback.router)


@app.get("/health")
def health():
    return {"status": "ok", "service": "performance"}
