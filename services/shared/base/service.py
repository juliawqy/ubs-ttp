"""Base service class — all application services inherit from this."""
from abc import ABC


class BaseService(ABC):
    """
    Base class for all service-layer classes.
    Enforces that subclasses are not instantiated directly
    and provides a consistent interface pattern.
    """
    pass
