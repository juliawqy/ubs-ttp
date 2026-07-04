"""
Abstract AI client interface.
"""
from abc import ABC, abstractmethod


class AbstractAIClient(ABC):
    """
    Abstract base class for all AI clients.
    Inject this type — never import ClaudeClient directly in services.
    """

    @abstractmethod
    async def check_bias(self, text: str) -> dict:
        """
        Analyse text for biased language.
        Returns dict: {flagged: bool, phrases: [{phrase, reason, suggestion}]}
        """
        ...

    @abstractmethod
    async def scan_ai_usage(self, resume_text: str) -> dict:
        """
        Detect AI-generated content in a resume.
        Returns dict: {ai_likely: bool, confidence: str, indicators: [str]}
        """
        ...

    def analyze_bias(self, text: str, context: str = "general") -> dict:
        """
        Deep bias analysis with category and severity enrichment.
        Returns dict: {flagged, phrases: [{phrase, reason, suggestion, category, severity}],
                       overall_suggestion}
        Non-abstract — subclasses opt in by overriding.
        Default raises NotImplementedError so callers can detect and fall back gracefully.
        """
        raise NotImplementedError(
            f"{type(self).__name__} does not implement analyze_bias. "
            "Use analyse_rule_based() as fallback."
        )
