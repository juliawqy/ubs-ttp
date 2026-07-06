"""
Abstract AI client interface.
All AI provider implementations must inherit from this class and implement
every abstract method.  Never import a concrete client (ClaudeClient, etc.)
directly in services — inject AbstractAIClient instead.
"""
from abc import ABC, abstractmethod


class AbstractAIClient(ABC):
    """
    Abstract base class for all AI clients.
    Inject this type — never import ClaudeClient directly in services.

    All three methods are abstract so that an incomplete implementation
    fails loudly at class-instantiation time rather than silently degrading
    at call time (fixes the LSP/ISP smell where analyze_bias was concrete
    and callers swallowed NotImplementedError as 'AI unavailable').
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

    @abstractmethod
    def analyze_bias(self, text: str, context: str = "general") -> dict:
        """
        Deep bias analysis with category and severity enrichment.
        Returns dict: {flagged, phrases: [{phrase, reason, suggestion, category, severity}],
                       overall_suggestion}
        """
        ...
