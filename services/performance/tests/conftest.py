"""
Pytest configuration for performance service tests.
Adds services/ to sys.path so `from shared.x import y` resolves both
locally (pytest from repo root) and inside Docker (/app/shared).
"""
import sys
from pathlib import Path

services_dir = Path(__file__).resolve().parents[2]
if str(services_dir) not in sys.path:
    sys.path.insert(0, str(services_dir))

import pytest


@pytest.fixture(autouse=True)
def reset_in_memory_state():
    """
    Clear module-level singleton state between tests.

    The router modules instantiate their services/stores once at import time
    (a FastAPI convention for in-memory backends). Without a reset, tests that
    share the same employee/rater IDs interfere with each other -- most visibly
    through the FeedbackService duplicate-submission guard, which turns a
    valid second POST into a 422 within the same test session.
    """
    # Import lazily so sys.path is already patched before the first import
    import app.routers.feedback as feedback_router
    import app.routers.reviews as reviews_router

    # Reset feedback store
    feedback_router._feedback_service._entries.clear()

    # Reset review store and its auto-increment counter
    reviews_router._store._store.clear()
    reviews_router._store._next_id = 1

    yield  # test runs here; no teardown required (cleared again before next test)
