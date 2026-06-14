"""
Bias analyser -- checks text for potentially biased language.
Used by: recruitment (justification check), performance (review check).
AI is called only when rule-based checks are insufficient.
"""
from __future__ import annotations

from .models import BiasAnalysisResult, FlaggedPhrase
from shared.base.service import BaseService
from shared.ai_client.abstract_client import AbstractAIClient

DEFAULT_RULE_BASED_FLAGS: dict[str, str] = {
    "rockstar": "Gendered/exclusionary tech jargon. Use 'high performer' instead.",
    "ninja": "Exclusionary jargon. Use 'expert' or 'specialist' instead.",
    "culture fit": "Vague and prone to affinity bias. Use 'values alignment' with specifics.",
    "aggressive": "Gendered connotation. Use 'driven' or 'results-oriented' instead.",
    "digital native": "Age-discriminatory. Specify the actual skill required instead.",
}


class BiasAnalyzer(BaseService):
    """
    Analyses text for biased language.
    Strategy: rule-based first, AI only if needed and explicitly requested.

    Args:
        rules: mapping of {phrase: "reason. suggestion"} to flag.
               Defaults to DEFAULT_RULE_BASED_FLAGS. Pass a custom dict to
               extend or replace patterns without subclassing (OCP).
        ai_client: optional AbstractAIClient implementation for deep analysis.
                   Injected, never created here (DIP / testability).
    """

    def __init__(
        self,
        rules: dict[str, str] | None = None,
        ai_client: AbstractAIClient | None = None,
    ):
        self._rules = rules if rules is not None else DEFAULT_RULE_BASED_FLAGS
        self._ai_client = ai_client

    def analyse_rule_based(self, text: str) -> BiasAnalysisResult:
        """
        Fast, deterministic check using known problematic patterns.
        No AI cost. Use this first.
        """
        flagged_phrases = []
        lower_text = text.lower()

        for phrase, reason_and_suggestion in self._rules.items():
            if phrase in lower_text:
                parts = reason_and_suggestion.split(". ", 1)
                flagged_phrases.append(FlaggedPhrase(
                    phrase=phrase,
                    reason=parts[0],
                    suggestion=parts[1] if len(parts) > 1 else "",
                ))

        return BiasAnalysisResult(
            flagged=len(flagged_phrases) > 0,
            flagged_phrases=flagged_phrases,
            ai_used=False,
        )

    async def analyse_with_ai(self, text: str) -> BiasAnalysisResult:
        """
        Deep analysis using Claude API.
        Only called when rule-based check passes but deeper analysis is needed.
        Requires ai_client to be injected.
        """
        if not self._ai_client:
            raise ValueError("AI client not configured. Use analyse_rule_based() instead.")
        return await self._ai_client.check_bias(text)
