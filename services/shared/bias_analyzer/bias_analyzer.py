"""
Bias analyser -- checks text for potentially biased language.
Used by: recruitment (justification check, job postings), performance (review check).
"""
from __future__ import annotations

from .models import BiasAnalysisResult, FlaggedPhrase
from shared.base.service import BaseService
from shared.ai_client.abstract_client import AbstractAIClient

DEFAULT_RULE_BASED_FLAGS: dict[str, str] = {
    "rockstar": "Gendered/exclusionary tech jargon that can deter applicants. Replace with 'high performer' or 'exceptional contributor'",
    "ninja": "Exclusionary jargon that may discourage diverse candidates. Replace with 'expert' or 'specialist'",
    "culture fit": "Vague criterion that often means 'similar to us', creating affinity bias. Replace with specific behaviours e.g. 'collaborates across teams' or 'communicates decisions transparently'",
    "aggressive": "Gendered connotation that can deter women from applying. Replace with 'driven', 'goal-oriented', or 'results-focused'",
    "digital native": "Age-discriminatory language that excludes older workers. Name the actual skill required e.g. 'proficient with Slack and Jira'",
}


class BiasAnalyzer(BaseService):
    """
    Analyses text for biased language.
    Strategy: AI analysis when client is injected, rule-based fallback otherwise.

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

    def analyse(self, text: str) -> BiasAnalysisResult:
        """
        Primary analysis method — calls Claude AI when a client is injected,
        falls back silently to rule-based on any exception or when no client
        is configured.

        This is the method all services should call. Use analyse_rule_based()
        directly only when you explicitly want to skip AI (e.g. in tests).
        """
        if self._ai_client is not None:
            try:
                raw = self._ai_client.analyze_bias(text)
                flagged_phrases = [
                    FlaggedPhrase(
                        phrase=p["phrase"],
                        reason=p.get("reason", ""),
                        suggestion=p.get("suggestion", ""),
                    )
                    for p in raw.get("phrases", [])
                ]
                return BiasAnalysisResult(
                    flagged=raw.get("flagged", len(flagged_phrases) > 0),
                    flagged_phrases=flagged_phrases,
                    ai_used=True,
                )
            except Exception:
                pass  # fall through to rule-based

        return self.analyse_rule_based(text)

    def analyse_rule_based(self, text: str) -> BiasAnalysisResult:
        """
        Fast, deterministic check using known problematic patterns.
        No AI cost. Called directly by analyse() as its fallback.
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
        Async deep analysis using Claude check_bias constraint.
        Kept for backward-compatibility; prefer analyse() for new code.
        """
        if not self._ai_client:
            raise ValueError("AI client not configured. Use analyse_rule_based() instead.")
        return await self._ai_client.check_bias(text)
