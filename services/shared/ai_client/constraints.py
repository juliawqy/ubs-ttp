"""
Defines strict constraints on what the AI is allowed to do and see.
Every AI call must pass through these constraints. No exceptions.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class AIConstraints:
    """
    Immutable constraint set for an AI operation.
    Defines allowed fields, token budget, and what the AI must NOT do.
    """
    operation: str          # e.g. "bias_check_review", "scan_ai_usage_resume"
    allowed_fields: tuple   # data fields permitted to be sent to Claude
    max_tokens: int         # hard cap on response tokens (cost control)
    system_prompt: str      # defines AI scope — what it can/cannot do


# Pre-defined constraint sets per operation
BIAS_CHECK_REVIEW = AIConstraints(
    operation="bias_check_review",
    allowed_fields=("review_text",),
    max_tokens=400,
    system_prompt=(
        "You are a bias detection assistant. Your ONLY job is to identify potentially "
        "biased language in performance review text. "
        "You may NOT make hiring or promotion decisions. "
        "You may NOT access or infer employee identity, demographics, or salary. "
        "Flag specific phrases and explain why each may reflect bias. "
        "Return JSON: {flagged: bool, phrases: [{phrase, reason, suggestion}]}. "
        "If no bias is detected, return {flagged: false, phrases: []}."
    ),
)

SCAN_AI_USAGE = AIConstraints(
    operation="scan_ai_usage_resume",
    allowed_fields=("resume_text",),
    max_tokens=200,
    system_prompt=(
        "You are reviewing a resume for signs of AI-generated content. "
        "You may NOT assess candidate quality, skills, or suitability. "
        "Return JSON: {ai_likely: bool, confidence: low|medium|high, indicators: [string]}."
    ),
)
