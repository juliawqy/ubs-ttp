"""
Root conftest for the analytics service test suite.
Resets the module-level in-memory store between every test so tests
are fully isolated from each other and from seed data mutations.
"""
import pytest


@pytest.fixture(autouse=True)
def reset_store():
    """Replace the router's singleton store with a fresh seeded instance."""
    from app.services.metrics_store import MetricsStore
    from app.routers import metrics as metrics_router

    metrics_router._store = MetricsStore()
    yield
    metrics_router._store = MetricsStore()
