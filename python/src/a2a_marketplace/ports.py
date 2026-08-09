"""Ports: the pluggable interfaces an operator implements.

This is the whole extensibility story (docs/platform-architecture/01). The
engine (Layer A) depends only on these ``typing.Protocol`` interfaces, never
on concrete infrastructure. An operator swaps in their own storage (Postgres,
Redis, Kafka), their own ranking (P10 — ranking is *theirs*, never the
protocol's), their own escrow/payment rail, and their own identity/KYC —
without forking the core.

Reference in-memory implementations live in ``adapters.py`` so the library
also runs out of the box.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Iterable, Protocol, runtime_checkable

from .models import (
    Agent,
    Commitment,
    Fulfillment,
    Intent,
    Money,
    Offer,
    Settlement,
)

Partition = tuple[tuple[str, str], ...]


@runtime_checkable
class Clock(Protocol):
    """Injected so time is testable/deterministic in simulation."""

    def now(self) -> datetime: ...


@runtime_checkable
class Storage(Protocol):
    """Persistence + the per-partition FIFO queues.

    The reference implementation is in-memory. A real deployment implements
    this over its own database and its own sharded queue; the engine does not
    care which, which is what lets it scale horizontally by partition.
    """

    def add_intent(self, intent: Intent) -> None: ...
    def add_offer(self, offer: Offer) -> None: ...
    def get_offer(self, offer_id: str) -> Offer | None: ...

    def queued_intents(self, category_ref: str, partition: Partition) -> list[Intent]:
        """Unmatched intents in the partition, in FIFO order (P6)."""

    def offers_in_partition(self, category_ref: str, partition: Partition) -> list[Offer]:
        """Offers in the partition with remaining capacity."""

    def save_commitment(self, commitment: Commitment) -> None: ...
    def save_fulfillment(self, fulfillment: Fulfillment) -> None: ...
    def save_settlement(self, settlement: Settlement) -> None: ...


@runtime_checkable
class RankingPolicy(Protocol):
    """Operator-owned (Layer B, P10). Given the constraint-passing candidate
    offers for an intent, return them best-first. The protocol NEVER ranks;
    two operators may rank completely differently and both are conformant."""

    def rank(self, intent: Intent, candidates: list[Offer]) -> list[Offer]: ...


@runtime_checkable
class EscrowProvider(Protocol):
    """Money movement, behind the P8 gates. A real deployment implements this
    over a payment rail (UPI, cards, AP2); the sim implementation just tracks
    balances. Money is only ever released via :meth:`release`, which the
    engine calls only after dual approval + platform verification."""

    def hold(self, commitment: Commitment) -> bool: ...
    def release(self, commitment: Commitment, net_to_provider: Money, fee: Money) -> None: ...
    def refund(self, commitment: Commitment) -> None: ...


@runtime_checkable
class IdentityVerifier(Protocol):
    """Onboarding fraud gate (P4). Real deployments plug KYC/attestation
    verification here; the reference implementation allows all (dev only)."""

    def verify(self, agent: Agent) -> bool: ...


@runtime_checkable
class Category(Protocol):
    """A vertical plugged in as data + behavior (docs/core-model/03). This is
    the ONLY place category-specific logic lives. Adding a new marketplace
    kind = implementing this Protocol, never touching the engine."""

    id: str

    def validate_intent(self, intent: Intent) -> None:
        """Raise on a malformed intent for this category (ext-schema check)."""

    def validate_offer(self, offer: Offer) -> None: ...

    def satisfies(self, intent: Intent, offer: Offer, now: datetime) -> bool:
        """Hard filter: does this offer meet this intent's constraints
        (price within budget, timing, capacity, category rules)?"""

    def price_for(self, intent: Intent, offer: Offer) -> Money:
        """The price this specific intent would pay for this offer."""

    def compatible(self, intents: Iterable[Intent]) -> bool:
        """Coalition compatibility (e.g. comfort prefs). Rejection reasons are
        never surfaced to the rejected party (docs/design.md §6)."""

    def verify_evidence(self, commitment: Commitment, evidence: dict[str, Any]) -> bool:
        """Platform-side P8 gate: does the evidence prove completion?"""
