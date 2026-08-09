"""Primitive value types and enums shared across the model.

These mirror ``schema/common.schema.json``. Kept dependency-free: plain
dataclasses and stdlib enums so the library imports with zero third-party
packages.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class Stance(str, Enum):
    """A role taken *per negotiation*, not a kind of agent (docs/core-model/01)."""

    DEMAND = "demand"
    SUPPLY = "supply"


class AutonomyLevel(str, Enum):
    """How much an agent may commit without a human. A human is simply an
    agent pinned to ``REQUIRE_CONFIRMATION`` (docs/spec/README)."""

    REQUIRE_CONFIRMATION = "require_confirmation"
    AUTO_COMMIT_WITHIN_SCOPE = "auto_commit_within_scope"


class EscrowState(str, Enum):
    AUTHORIZED = "authorized"
    HELD = "held"
    RELEASED = "released"
    REFUNDED = "refunded"
    DISPUTED = "disputed"


class CommitmentStatus(str, Enum):
    HELD = "held"
    CONFIRMED = "confirmed"
    EXPIRED = "expired"
    RENEGED = "reneged"


class CoalitionStatus(str, Enum):
    FORMING = "forming"
    NEGOTIATING = "negotiating"
    PROPOSED = "proposed"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    EXPIRED = "expired"
    DISSOLVED = "dissolved"


class FulfillmentOutcome(str, Enum):
    COMPLETED = "completed"
    PARTIAL = "partial"
    FAILED = "failed"
    DISPUTED = "disputed"


class PriceRule(str, Enum):
    ADDITIVE = "additive"
    PROPORTIONAL_SPLIT = "proportional_split"


@dataclass(frozen=True, slots=True)
class Money:
    """Integer minor units + ISO-4217 currency. Never floats for money."""

    amount_minor: int
    currency: str

    def __post_init__(self) -> None:
        if self.amount_minor < 0:
            raise ValueError("Money.amount_minor must be non-negative")
        if len(self.currency) != 3 or not self.currency.isupper():
            raise ValueError("Money.currency must be a 3-letter ISO-4217 code")

    def __add__(self, other: "Money") -> "Money":
        self._same_currency(other)
        return Money(self.amount_minor + other.amount_minor, self.currency)

    def __le__(self, other: "Money") -> bool:
        self._same_currency(other)
        return self.amount_minor <= other.amount_minor

    def __lt__(self, other: "Money") -> bool:
        self._same_currency(other)
        return self.amount_minor < other.amount_minor

    def times(self, n: int) -> "Money":
        return Money(self.amount_minor * n, self.currency)

    def bps(self, basis_points: int) -> "Money":
        """A fee in basis points, rounded down (never over-charges)."""
        return Money(self.amount_minor * basis_points // 10_000, self.currency)

    def minus(self, other: "Money") -> "Money":
        self._same_currency(other)
        return Money(self.amount_minor - other.amount_minor, self.currency)

    def _same_currency(self, other: "Money") -> None:
        if self.currency != other.currency:
            raise ValueError(f"currency mismatch: {self.currency} vs {other.currency}")


@dataclass(frozen=True, slots=True)
class TimeWindow:
    earliest: datetime
    latest: datetime

    def __post_init__(self) -> None:
        if self.earliest > self.latest:
            raise ValueError("TimeWindow.earliest must be <= latest")

    def contains(self, when: datetime) -> bool:
        return self.earliest <= when <= self.latest
