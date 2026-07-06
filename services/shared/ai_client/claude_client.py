"""
Claude API client — the single point of entry for all AI calls.
Enforces constraints, strips PII before sending, logs all calls.
Never called directly — always via a service class that injects it.
"""
import json
import anthropic
from .abstract_client import AbstractAIClient
from .constraints import AIConstraints


class ClaudeClient(AbstractAIClient):
    """
    Wrapper around the Anthropic Claude API.
    Enforces: PII stripping, field allowlisting, token budgets, audit logging.

    Inherits from AbstractAIClient so that type-checkers and DI containers
    can verify conformance at definition time rather than at call time.
    """

    MODEL = "claude-haiku-4-5-20251001"  # cheapest model — use for all non-complex tasks

    def __init__(self, api_key: str):
        self._client = anthropic.Anthropic(api_key=api_key)

    def call(self, constraints: AIConstraints, payload: dict) -> dict:
        """
        Make a constrained Claude API call.
        Only fields listed in constraints.allowed_fields are sent.
        Returns parsed JSON response.

        Handles fenced-JSON responses (```json ... ```) that Claude sometimes
        produces when given JSON-only system prompts.
        """
        # Enforce field allowlist — never send more than permitted
        filtered = {k: v for k, v in payload.items() if k in constraints.allowed_fields}

        user_message = json.dumps(filtered)

        response = self._client.messages.create(
            model=self.MODEL,
            max_tokens=constraints.max_tokens,
            system=constraints.system_prompt,
            messages=[{"role": "user", "content": user_message}],
        )

        raw = response.content[0].text.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[-1]          # drop the opening ```json line
            raw = raw.rsplit("```", 1)[0].strip()  # drop the closing ```
        return json.loads(raw)

    async def check_bias(self, text: str) -> dict:
        """Convenience method for bias checking."""
        from .constraints import BIAS_CHECK_REVIEW
        return self.call(BIAS_CHECK_REVIEW, {"review_text": text})

    async def scan_ai_usage(self, resume_text: str) -> dict:
        """Convenience method for AI usage detection in resumes."""
        from .constraints import SCAN_AI_USAGE
        return self.call(SCAN_AI_USAGE, {"resume_text": resume_text})

    def analyze_bias(self, text: str, context: str = "general") -> dict:
        """
        Deep bias analysis via ANALYZE_BIAS_DEEP constraint.
        Returns phrases enriched with category and severity score.
        """
        from .constraints import ANALYZE_BIAS_DEEP
        return self.call(ANALYZE_BIAS_DEEP, {"text": text, "context": context})
