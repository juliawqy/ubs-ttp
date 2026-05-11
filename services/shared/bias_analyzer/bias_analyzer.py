"""
Bias analyser — checks text for potentially biased language.
Used by: recruitment (justification check), performance (review check).
AI is called only when rule-based checks are insufficient.
"""
from .models import BiasAnalysisResult, FlaggedPhrase
from shared.base.service import BaseService

# Rule-based patterns checked before AI is invoked (cheaper, deterministic)
RULE_BASED_FLAGS = {
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
    """

    def __init__(self, ai_client=None):
        # ai_client is optional — injected, not created here (DI / testability)
        self._ai_client = ai_client

    def analyse_rule_based(self, text: str) -> BiasAnalysisResult:
        """
        Fast, deterministic check using known problematic patterns.
        No AI cost. Use this first.
        """
        flagged_phrases = []
        lower_text = text.lower()

        for phrase, reason_and_suggestion in RULE_BASED_FLAGS.items():
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
