"""
Single factory for creating an AbstractAIClient from the environment.

Call make_ai_client() — never import ClaudeClient directly in services or
routers.  Adding a second AI provider means updating only this file.
"""
import os
from shared.ai_client.abstract_client import AbstractAIClient


def make_ai_client() -> AbstractAIClient | None:
    """
    Returns a configured ClaudeClient when ANTHROPIC_API_KEY is set in the
    environment, otherwise None.

    BiasAnalyzer(ai_client=None) falls back to rule-based analysis, so
    returning None is safe for any caller that uses BiasAnalyzer.

    The ClaudeClient import is deferred to avoid importing anthropic when
    no key is present (test environments that have no AI dependency).
    """
    key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not key:
        return None
    from shared.ai_client.claude_client import ClaudeClient
    return ClaudeClient(key)
