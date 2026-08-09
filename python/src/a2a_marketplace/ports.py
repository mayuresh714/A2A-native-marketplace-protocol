"""Ports: the pluggable interfaces an operator implements.

This is the whole extensibility story (docs/platform-architecture/01). The
engine (Layer A) depends only on these ``typing.Protocol`` interfaces, never
on concrete infrastructure. An operator swaps in their own storage (Postgres,
Redis, Kafka), their own ranking (P10 — ranking is *theirs*, never the
protocol's), their own escrow/payment rail, their own identity/KYC, and their
own dispute-resolution policy (Layer C) — without forking the core.

Reference in-memory implementations live in ``adapters.py`` so the library
also runs out of the box.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Iterable, Protocol, runtime_checkable

from .models import (
    Agent,
    Commitment,
    Dispute,
    Fulfillment,
    Intent,
    MatchProposal,
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
    """Persistence + the per-partition, per-stance FIFO queues (P11: demand
    and supply are separate queues, both keyed by the same partition).

    The reference implementation is in-memory. A real deployment implements
    this over its own database and its own sharded queue; the engine does not
    care which, which is what lets it scale horizontally by partition.
    """

    def add_intent(self, intent: Intent) -> None: ...
    def add_offer(self, offer: Offer) -> None: ...
    def get_offer(self, offer_id: str) -> Offer | None: ...
    def get_intent(self, intent_id: str) -> Intent | None: ...

    def demand_queue(self, category_ref: str, partition: Partition) -> list[Intent]:
        """Unmatched intents in the partition, in FIFO order (P6)."""

    def supply_queue(self, category_ref: str, partition: Partition) -> list[Offer]:
        """Offers in the partition with remaining capacity."""

    def save_proposal(self, proposal: MatchProposal) -> None: ...
    def save_commitment(self, commitment: Commitment) -> None: ...
    def save_fulfillment(self, fulfillment: Fulfillment) -> None: ...
    def save_settlement(self, settlement: Settlement) -> None: ...
    def save_dispute(self, dispute: Dispute) -> None: ...


@runtime_checkable
class RankingPolicy(Protocol):
    """Operator-owned (Layer B, P10). Given the constraint-passing candidate
    offers for an intent, return them best-first. The protocol NEVER ranks;
    two operators may rank completely differently and both are conformant."""

    def rank(self, intent: Intent, candidates: list[Offer]) -> list[Offer]: ...


@runtime_checkable
class EscrowProvider(Protocol):
    """Money movement, always in PLATFORM CUSTODY — the operator holds funds,
    not a third-party clearing exchange (P11). A real deployment implements
    this over a payment rail (UPI, cards, AP2); the sim implementation just
    tracks balances.

    ``hold`` captures the consumer's payment and (if the offer specifies one)
    the provider's stake, atomically with Commitment formation — this is what
    "each party putting money in" means concretely.

    ``payout`` is the single, general money-movement primitive: an arbitrary
    distribution of the held total across agent ids, summing to what was
    held. Normal settlement is one kind of payout (net to provider, fee to
    the platform); a dispute resolution's split is another (docs/spec/05
    §5) — same mechanism, different distribution, decided by whoever calls
    it (the engine for normal settlement, the DisputeResolver's outcome for
    a dispute).
    """

    def hold(self, commitment: Commitment) -> bool: ...
    def payout(self, commitment: Commitment, payouts: dict[str, Money]) -> None: ...


@runtime_checkable
class IdentityVerifier(Protocol):
    """Onboarding fraud gate (P4). Real deployments plug KYC/attestation
    verification here; the reference implementation allows all (dev only)."""

    def verify(self, agent: Agent) -> bool: ...


@runtime_checkable
class RequestFraudFilter(Protocol):
    """Per-REQUEST fraud/governance filtering (P11), distinct from the
    one-time IdentityVerifier onboarding gate: this runs on every Intent and
    Offer before it's admitted to a queue, catching an already-verified
    agent that starts spawning fraudulent requests after onboarding."""

    def allow_intent(self, intent: Intent) -> bool: ...
    def allow_offer(self, offer: Offer) -> bool: ...


@runtime_checkable
class Notifier(Protocol):
    """Notification hook (P11: "notify parties"). A real deployment wires
    this to push/webhook/SMS; the reference implementation just logs."""

    def notify(self, agent_id: str, event: str, payload: dict[str, Any]) -> None: ...


@runtime_checkable
class DisputeResolver(Protocol):
    """Layer C / operator policy (docs/spec/05). The protocol guarantees the
    dispute STATE MACHINE (freeze on raise, audit trail, closed outcome
    vocabulary); this port is where an operator's actual adjudication rules
    plug in. The reference implementation does not decide anything — it
    always escalates, which is a legitimate (if minimal) policy."""

    def resolve(self, dispute: Dispute, commitment: Commitment) -> Dispute:
        """Return the dispute updated with .status, .outcome, .payouts set."""


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
