"""
Bias classifier service for the ai-assistant.
Delegates to shared.bias_analyzer — no duplicate logic here.
"""
from pydantic_settings import BaseSettings
from shared.ai_client import ClaudeClient
from shared.bias_analyzer import BiasAnalyzer


class Settings(BaseSettings):
    anthropic_api_key: str = ""

    class Config:
        env_file = ".env"


def get_bias_classifier() -> BiasAnalyzer:
    """Factory — returns BiasAnalyzer with Claude injected if API key is set."""
    settings = Settings()
    ai_client = ClaudeClient(settings.anthropic_api_key) if settings.anthropic_api_key else None
    return BiasAnalyzer(ai_client=ai_client)
