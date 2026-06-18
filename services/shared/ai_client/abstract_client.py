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
