"""Typed errors raised by the engine."""
from __future__ import annotations


class MarketplaceError(Exception):
    """Base class for all library errors."""


class UnknownCategoryError(MarketplaceError):
    pass


class IdentityRejectedError(MarketplaceError):
    pass


class MandateViolationError(MarketplaceError):
    """A commitment would exceed the authorizing mandate's scope (P8)."""


class ValidationError(MarketplaceError):
    pass
