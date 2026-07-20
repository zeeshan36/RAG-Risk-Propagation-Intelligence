"""Shared exception hierarchy."""


class RiskPropagationError(Exception):
    """Base exception for the risk propagation system."""


class ConfigMisconfigurationError(RiskPropagationError):
    """Raised when configuration values are inconsistent or invalid."""


class RepositoryError(RiskPropagationError):
    """Raised when an in-memory repository operation fails."""


class EventProcessingError(RiskPropagationError):
    """Raised when event classification or propagation fails."""


class DependencyNotAvailableError(RiskPropagationError):
    """Raised when an optional dependency is required but not installed."""
