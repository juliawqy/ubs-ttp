"""Base service class -- organisational marker inherited by all service-layer classes."""


class BaseService:
    """
    Marker base class for all application service classes.

    This is a plain (non-abstract) base used purely for organisational
    consistency -- it makes grep/IDE navigation easier and gives a common
    hook point if cross-cutting behaviour (e.g. audit logging, tracing) is
    added later.

    It does NOT enforce any interface contract. Services that need an
    enforced abstract interface (e.g. NotificationService) define their
    own ABC separately.
    """
