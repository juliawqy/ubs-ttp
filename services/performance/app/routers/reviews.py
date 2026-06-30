"""
Reviews router.
POST /reviews             -- submit a review (rubric scores + comments); returns
                             the score breakdown and a per-criterion bias check
GET  /reviews             -- list all submitted reviews
GET  /reviews/rubric      -- the fixed set of rubric criteria (key + description)
                             plus score bounds, so the frontend form never has
                             to hardcode them (mirrors training's
                             GET /training/iat/categories)
GET  /reviews/{id}        -- retrieve a single review by ID
POST /reviews/check-bias  -- pre-check free text for bias without recording a
                             review (frontend's live bias warnings, mirrors
                             recruitment's /candidates/check-justification-bias)
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from shared.bias_analyzer.bias_analyzer import BiasAnalyzer, BiasAnalysisResult
from app.models import CriterionScore, Review, RUBRIC_CRITERIA, MIN_SCORE, MAX_SCORE
from app.services.review import ReviewService

router = APIRouter(prefix="/reviews", tags=["reviews"])

_bias_analyzer = BiasAnalyzer()
_review_service = ReviewService(bias_analyzer=_bias_analyzer)


# -- in-memory store ------------------------------------------------------------

class ReviewStore:
    """Owns review persistence only. Swap for a DB-backed impl without touching the router."""

    def __init__(self) -> None:
        self._store: dict[int, Review] = {}
        self._next_id: int = 1

    def add(self, review: Review) -> int:
        """Store a newly submitted review. Returns the assigned review_id."""
        review_id = self._next_id
        self._store[review_id] = review
        self._next_id += 1
        return review_id

    def get(self, review_id: int) -> Review | None:
        return self._store.get(review_id)

    def list_all(self) -> list[tuple[int, Review]]:
        return list(self._store.items())


_store = ReviewStore()


# -- schemas ---------------------------------------------------------------------

class CriterionScoreIn(BaseModel):
    criterion: str
    score: int
    comments: str = ""


class ReviewCreate(BaseModel):
    employee_id: str
    reviewer_id: str
    criteria: list[CriterionScoreIn]


class BiasCheckTextRequest(BaseModel):
    text: str


# -- helpers ----------------------------------------------------------------------

def _bias_check_to_dict(result: BiasAnalysisResult) -> dict:
    return {
        "flagged": result.flagged,
        "flagged_phrases": [
            {"phrase": fp.phrase, "reason": fp.reason, "suggestion": fp.suggestion}
            for fp in result.flagged_phrases
        ],
        "ai_used": result.ai_used,
    }


def _review_to_dict(review_id: int, review: Review) -> dict:
    return {
        "id": review_id,
        "employee_id": review.employee_id,
        "reviewer_id": review.reviewer_id,
        "criteria": [
            {"criterion": c.criterion, "score": c.score, "comments": c.comments}
            for c in review.criteria
        ],
        "score": {
            "per_criterion": review.score.per_criterion,
            "average": review.score.average,
        },
        "bias_checks": {
            criterion: _bias_check_to_dict(result)
            for criterion, result in review.bias_checks.items()
        },
    }


# -- routes -----------------------------------------------------------------------

@router.post("", status_code=201, responses={422: {"description": "Invalid review submission"}})
def create_review(body: ReviewCreate):
    criteria = [
        CriterionScore(criterion=c.criterion, score=c.score, comments=c.comments)
        for c in body.criteria
    ]
    try:
        review = _review_service.submit(body.employee_id, body.reviewer_id, criteria)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    review_id = _store.add(review)
    return _review_to_dict(review_id, review)


@router.get("")
def list_reviews():
    return [_review_to_dict(review_id, review) for review_id, review in _store.list_all()]


@router.get("/rubric")
def get_rubric():
    """
    Registered before /{review_id} -- GET /reviews/{review_id} declares an
    int path param, and Starlette tries routes in registration order, so
    "rubric" must be matched here first or it would fall through to the
    id route and fail int conversion.
    """
    return {
        "criteria": [
            {"key": key, "description": description}
            for key, description in RUBRIC_CRITERIA.items()
        ],
        "min_score": MIN_SCORE,
        "max_score": MAX_SCORE,
    }


@router.get("/{review_id}", responses={404: {"description": "Review not found"}})
def get_review(review_id: int):
    review = _store.get(review_id)
    if review is None:
        raise HTTPException(status_code=404, detail="Review not found")
    return _review_to_dict(review_id, review)


@router.post("/check-bias")
def check_bias(body: BiasCheckTextRequest):
    """Pre-check free text for bias without recording any review."""
    result = _bias_analyzer.analyse_rule_based(body.text)
    return _bias_check_to_dict(result)
