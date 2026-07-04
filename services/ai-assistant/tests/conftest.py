"""
Pytest configuration for ai-assistant service tests.
Adds services/ to sys.path so `from shared.x import y` resolves both
locally (pytest from repo root) and inside Docker (/app/shared).

For unit tests we override the get_service FastAPI dependency with a
rule-based-only BiasDetectionService (no AI client). This lets the HTTP
layer tests run deterministically without an API key.
Integration tests (tests/integration/) inject their own mock clients
directly into BiasDetectionService and bypass the HTTP layer entirely.
"""
import sys
from pathlib import Path

services_dir = Path(__file__).resolve().parents[2]
if str(services_dir) not in sys.path:
    sys.path.insert(0, str(services_dir))

import pytest
from app.main import app
from app.routers.assistant import get_service
from app.services.bias_classifier import BiasDetectionService


def _rule_based_service() -> BiasDetectionService:
    """No AI client — deterministic rule-based only. Used in unit tests."""
    return BiasDetectionService(ai_client=None)


@pytest.fixture(autouse=True)
def override_ai_dependency():
    """
    Replace the real ClaudeClient dependency with a rule-based stub for all
    unit tests. Integration tests that need a mock Claude client construct
    BiasDetectionService directly and never go through this fixture.
    """
    app.dependency_overrides[get_service] = _rule_based_service
    yield
    app.dependency_overrides.clear()
