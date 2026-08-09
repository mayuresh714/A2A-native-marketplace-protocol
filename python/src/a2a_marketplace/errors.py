"""Typed errors raised by the engine."""
from __future__ import annotations


class MarketplaceError(Exception):
    """Base class for all library errors."""


class UnknownCategoryError(MarketplaceError):
    pass


class IdentityRejectedError(MarketplaceError):
    """Onboarding-time identity/Sybil check failed (P4)."""


class RequestRejectedError(MarketplaceError):
    """Per-request fraud filter rejected an Intent or Offer before it
    entered a queue (P11), distinct from onboarding rejection."""


class MandateViolationError(MarketplaceError):
    """A commitment would exceed the authorizing mandate's scope (P8)."""


class DisputeInProgressError(MarketplaceError):
    """Raised when an operation that requires undisputed escrow (fulfilling,
    raising a second dispute) is attempted while a dispute is open (docs/spec/05)."""


class ValidationError(MarketplaceError):
    pass
