"""
Bias analyser -- checks text for potentially biased language.
Used by: recruitment (justification check, job postings), performance (review check).
"""
from __future__ import annotations
import logging
import re
from typing import NamedTuple

from .models import BiasAnalysisResult, FlaggedPhrase
from shared.base.service import BaseService
from shared.ai_client.abstract_client import AbstractAIClient

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# String-based rules: simple substring matching, case-insensitive via .lower()
# ---------------------------------------------------------------------------
DEFAULT_RULE_BASED_FLAGS: dict[str, str] = {
    "rockstar": "Gendered/exclusionary tech jargon that can deter applicants. Replace with 'high performer' or 'exceptional contributor'",
    "ninja": "Exclusionary jargon that may discourage diverse candidates. Replace with 'expert' or 'specialist'",
    "culture fit": "Vague criterion that often means 'similar to us', creating affinity bias. Replace with specific behaviours e.g. 'collaborates across teams' or 'communicates decisions transparently'",
    "cultural fit": "Vague criterion that often means 'similar to us', creating affinity bias. Replace with specific behaviours e.g. 'collaborates across teams' or 'communicates decisions transparently'",
    "aggressive": "Gendered connotation that can deter women from applying. Replace with 'driven', 'goal-oriented', or 'results-focused'",
    "digital native": "Age-discriminatory language that excludes older workers. Name the actual skill required e.g. 'proficient with Slack and Jira'",
    "not a good fit": "Vague rejection criterion that can mask unconscious bias. Replace with specific, observable behaviours or skill gaps",
    "doesn't fit": "Vague criterion that can mask unconscious bias. Replace with specific, observable behaviours or skill gaps",
}


# ---------------------------------------------------------------------------
# Regex-based rules: catch structural discrimination patterns that cannot be
# caught by simple substring matching (e.g. "only [any nationality] applicants")
# ---------------------------------------------------------------------------
class _RegexRule(NamedTuple):
    pattern: re.Pattern
    display_phrase: str   # shown in the flagged_phrases list
    reason: str
    suggestion: str


DEFAULT_REGEX_FLAGS: list[_RegexRule] = [
    _RegexRule(
        pattern=re.compile(r"\bonly\s+\w+\s+applicants?\b", re.IGNORECASE),
        display_phrase="only [nationality] applicants",
        reason="Restricts applicants by nationality/origin, which is illegal discrimination in most jurisdictions",
        suggestion="Remove nationality/origin restrictions; evaluate candidates on skills and qualifications only",
    ),
    _RegexRule(
        pattern=re.compile(r"\b(no|not)\s+(foreigners?|immigrants?|expats?)\b", re.IGNORECASE),
        display_phrase="no foreigners / no immigrants",
        reason="Discriminates against candidates based on national origin",
        suggestion="Remove national origin restrictions; evaluate candidates on skills and qualifications only",
    ),
    _RegexRule(
        pattern=re.compile(
            r"\blocals?\s+only\b|\blocal\s+candidates?\s+only\b",
            re.IGNORECASE,
        ),
        display_phrase="locals only / local candidates only",
        reason="May discriminate against candidates based on national origin or ethnicity",
        suggestion="Consider remote candidates or state the legitimate business reason (e.g. required on-site presence)",
    ),
    _RegexRule(
        pattern=re.compile(
            r"\b(citizens?\s+only|nationals?\s+only)\b",
            re.IGNORECASE,
        ),
        display_phrase="citizens only / nationals only",
        reason="Restricts applicants by citizenship, which may constitute illegal discrimination unless a legal exemption applies",
        suggestion="Specify the legitimate legal requirement (e.g. government security clearance) rather than a blanket exclusion",
    ),
]


class BiasAnalyzer(BaseService):
    """
    Analyses text for biased language.
    Strategy: AI analysis when client is injected, rule-based fallback otherwise.

    Args:
        rules: mapping of {phrase: "reason. suggestion"} to flag.
               Defaults to DEFAULT_RULE_BASED_FLAGS. Pass a custom dict to
               extend or replace patterns without subclassing (OCP).
        regex_rules: list of _RegexRule for structural patterns that string
                     matching cannot catch (e.g. "only [any nationality] applicants").
                     Defaults to DEFAULT_REGEX_FLAGS.
        ai_client: optional AbstractAIClient implementation for deep analysis.
                   Injected, never created here (DIP / testability).
    """

    def __init__(
        self,
        rules: dict[str, str] | None = None,
        regex_rules: list[_RegexRule] | None = None,
        ai_client: AbstractAIClient | None = None,
    ):
        self._rules = rules if rules is not None else DEFAULT_RULE_BASED_FLAGS
        self._regex_rules = regex_rules if regex_rules is not None else DEFAULT_REGEX_FLAGS
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
            except Exception as exc:
                logger.warning("BiasAnalyzer AI call failed, falling back to rule-based: %s", exc)

        return self.analyse_rule_based(text)

    def analyse_rule_based(self, text: str) -> BiasAnalysisResult:
        """
        Fast, deterministic check using known problematic patterns.
        Combines simple substring matching with regex pattern detection.
        No AI cost. Called directly by analyse() as its fallback.
        """
        flagged_phrases: list[FlaggedPhrase] = []
        lower_text = text.lower()

        for phrase, reason_and_suggestion in self._rules.items():
            if phrase in lower_text:
                parts = reason_and_suggestion.split(". ", 1)
                flagged_phrases.append(FlaggedPhrase(
                    phrase=phrase,
                    reason=parts[0],
                    suggestion=parts[1] if len(parts) > 1 else "",
                ))

        for rule in self._regex_rules:
            if rule.pattern.search(text):
                flagged_phrases.append(FlaggedPhrase(
                    phrase=rule.display_phrase,
                    reason=rule.reason,
                    suggestion=rule.suggestion,
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
