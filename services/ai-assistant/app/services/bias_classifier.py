"""
BiasDetectionService — orchestrates rule-based + optional AI bias analysis.

Design:
  1. Rule-based check via shared BiasAnalyzer (always runs; free, deterministic).
  2. If an AI client is injected, calls client.analyze_bias() for richer output
     (category, severity, overall_suggestion from Claude).
  3. On any AI exception the service falls back silently to rule-based results.
  4. Rule-based results are always enriched with category/severity via
     BIAS_PHRASE_CATALOG — so even the fallback path returns structured data.

SOLID notes:
  - SRP: service owns analysis orchestration only; router owns HTTP; models own data.
  - OCP: extend BIAS_PHRASE_CATALOG without touching service logic.
  - DIP: AbstractAIClient injected — never imported directly.
"""
from __future__ import annotations

from shared.bias_analyzer import BiasAnalyzer
from app.models import AnalysisResult, BiasCategory, EnrichedFlaggedPhrase

# ---------------------------------------------------------------------------
# Phrase catalog — maps known biased phrases to category + severity.
# Used to enrich rule-based FlaggedPhrase objects, which carry only
# reason/suggestion from the shared BiasAnalyzer.
# ---------------------------------------------------------------------------
BIAS_PHRASE_CATALOG: dict[str, dict] = {
    # gender
    "rockstar":       {"category": BiasCategory.gender,        "severity": 2},
    "ninja":          {"category": BiasCategory.gender,        "severity": 2},
    "aggressive":     {"category": BiasCategory.gender,        "severity": 2},
    "manpower":       {"category": BiasCategory.gender,        "severity": 1},
    "chairman":       {"category": BiasCategory.gender,        "severity": 1},
    "he or she":      {"category": BiasCategory.gender,        "severity": 1},
    # age
    "digital native": {"category": BiasCategory.age,           "severity": 3},
    "young and dynamic": {"category": BiasCategory.age,        "severity": 3},
    "recent graduate":   {"category": BiasCategory.age,        "severity": 2},
    # ethnicity / cultural
    "native speaker": {"category": BiasCategory.ethnicity,     "severity": 2},
    "articulate":     {"category": BiasCategory.ethnicity,     "severity": 2},
    # general (catch-all for vague exclusionary criteria)
    "culture fit":    {"category": BiasCategory.general,       "severity": 3},
    "not a culture fit": {"category": BiasCategory.general,    "severity": 3},
}

_DEFAULT_CATEGORY = BiasCategory.general
_DEFAULT_SEVERITY = 1


class BiasDetectionService:
    """
    Analyse text for biased language, returning enriched results.

    Args:
        bias_analyzer: shared rule-based analyzer (defaults to a fresh instance).
        ai_client: optional AI client for deep analysis.
                   Must implement analyze_bias(text, context) -> dict.
                   Injected — never created here (DIP / testability).
    """

    def __init__(
        self,
        bias_analyzer: BiasAnalyzer | None = None,
        ai_client=None,
    ):
        self._analyzer = bias_analyzer if bias_analyzer is not None else BiasAnalyzer()
        self._ai_client = ai_client

    def analyze(self, text: str, context: str = "general") -> AnalysisResult:
        """
        Analyse text for bias.

        Tries AI first when client is available; falls back to rule-based
        on any exception. Rule-based results are always enriched with
        category/severity from BIAS_PHRASE_CATALOG.
        """
        if self._ai_client is not None:
            try:
                return self._analyze_with_ai(text, context)
            except Exception:
                # Graceful degradation: API down, quota exceeded, parse error, etc.
                pass

        return self._analyze_rule_based(text)

    # -- private ---------------------------------------------------------------

    def _analyze_with_ai(self, text: str, context: str) -> AnalysisResult:
        raw = self._ai_client.analyze_bias(text, context)
        phrases = [
            EnrichedFlaggedPhrase(
                phrase=p["phrase"],
                reason=p.get("reason", ""),
                suggestion=p.get("suggestion", ""),
                category=BiasCategory.from_str(p.get("category", "general")),
                severity=int(p.get("severity", _DEFAULT_SEVERITY)),
            )
            for p in raw.get("phrases", [])
        ]
        return AnalysisResult(
            flagged=raw.get("flagged", len(phrases) > 0),
            flagged_phrases=phrases,
            overall_suggestion=raw.get("overall_suggestion"),
            ai_used=True,
        )

    def _analyze_rule_based(self, text: str) -> AnalysisResult:
        result = self._analyzer.analyse_rule_based(text)
        phrases = [
            EnrichedFlaggedPhrase(
                phrase=fp.phrase,
                reason=fp.reason,
                suggestion=fp.suggestion,
                category=BIAS_PHRASE_CATALOG.get(fp.phrase, {}).get(
                    "category", _DEFAULT_CATEGORY
                ),
                severity=BIAS_PHRASE_CATALOG.get(fp.phrase, {}).get(
                    "severity", _DEFAULT_SEVERITY
                ),
            )
            for fp in result.flagged_phrases
        ]
        return AnalysisResult(
            flagged=result.flagged,
            flagged_phrases=phrases,
            overall_suggestion=None,
            ai_used=False,
        )
