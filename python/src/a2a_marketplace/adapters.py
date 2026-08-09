"""Reference adapters: minimal in-memory implementations of every port.

These make the library run out of the box for development, testing, and
simulation. A production operator replaces each with their own infra
(Postgres/Redis storage, a real payment rail, real KYC, a real dispute-
adjudication policy) — the engine is unchanged. Everything here is
intentionally simple, not performant.
"""
from __future__ import annotations

from datetime import datetime, timezone

from .models import (
    Agent,
    Commitment,
    Dispute,
    DisputeOutcome,
    DisputeStatus,
    Fulfillment,
    Intent,
    MatchProposal,
    Money,
    Offer,
    Settlement,
)
from .ports import Partition


class SystemClock:
    def now(self) -> datetime:
        return datetime.now(timezone.utc)


class FixedClock:
    """Deterministic clock for tests/simulation."""

    def __init__(self, moment: datetime) -> None:
        self._moment = moment

    def now(self) -> datetime:
        return self._moment

    def set(self, moment: datetime) -> None:
        self._moment = moment

    def advance(self, **kwargs) -> None:
        from datetime import timedelta

        self._moment = self._moment + timedelta(**kwargs)


class InMemoryStorage:
    def __init__(self) -> None:
        self._intents: dict[str, Intent] = {}
        self._offers: dict[str, Offer] = {}
        self.proposals: dict[str, MatchProposal] = {}
        self.commitments: dict[str, Commitment] = {}
        self.fulfillments: dict[str, Fulfillment] = {}
        self.settlements: dict[str, Settlement] = {}
        self.disputes: dict[str, Dispute] = {}

    def add_intent(self, intent: Intent) -> None:
        self._intents[intent.intent_id] = intent

    def add_offer(self, offer: Offer) -> None:
        self._offers[offer.offer_id] = offer

    def get_offer(self, offer_id: str) -> Offer | None:
        return self._offers.get(offer_id)

    def get_intent(self, intent_id: str) -> Intent | None:
        return self._intents.get(intent_id)

    def demand_queue(self, category_ref: str, partition: Partition) -> list[Intent]:
        items = [
            i
            for i in self._intents.values()
            if i.category_ref == category_ref and i.partition == partition and not i.matched
        ]
        # FIFO: earliest created first (P6).
        return sorted(items, key=lambda i: i.created_at)

    def supply_queue(self, category_ref: str, partition: Partition) -> list[Offer]:
        return [
            o
            for o in self._offers.values()
            if o.category_ref == category_ref and o.partition == partition
        ]

    def save_proposal(self, proposal: MatchProposal) -> None:
        self.proposals[proposal.proposal_id] = proposal

    def save_commitment(self, commitment: Commitment) -> None:
        self.commitments[commitment.commitment_id] = commitment

    def save_fulfillment(self, fulfillment: Fulfillment) -> None:
        self.fulfillments[fulfillment.fulfillment_id] = fulfillment

    def save_settlement(self, settlement: Settlement) -> None:
        self.settlements[settlement.settlement_id] = settlement

    def save_dispute(self, dispute: Dispute) -> None:
        self.disputes[dispute.dispute_id] = dispute


class PriceAscRanking:
    """A trivial, neutral default: cheapest first. It exists only so the
    library runs unconfigured. Real operators inject their own RankingPolicy
    (by ETA, quality, strategy, ...) — ranking is theirs, not the protocol's
    (P10)."""

    def rank(self, intent: Intent, candidates: list[Offer]) -> list[Offer]:
        return sorted(candidates, key=lambda o: o.price.amount_minor)


class SimEscrow:
    """Simulated escrow: platform-custody bookkeeping, no real money.
    ``held`` tracks the total captured (consumer amount + any provider
    stake) per commitment; ``payout`` distributes it and clears the hold."""

    def __init__(self) -> None:
        self.held: dict[str, Money] = {}
        self.payouts: dict[str, dict[str, Money]] = {}

    def hold(self, commitment: Commitment) -> bool:
        total = commitment.escrow.amount
        if commitment.escrow.provider_stake is not None:
            total = total + commitment.escrow.provider_stake
        self.held[commitment.commitment_id] = total
        return True

    def payout(self, commitment: Commitment, payouts: dict[str, Money]) -> None:
        held = self.held.pop(commitment.commitment_id, None)
        if held is not None and payouts:
            total_out = None
            for m in payouts.values():
                total_out = m if total_out is None else total_out + m
            if total_out is not None and total_out.amount_minor > held.amount_minor:
                raise ValueError("payout exceeds held escrow")
        self.payouts[commitment.commitment_id] = dict(payouts)


class AllowAllIdentity:
    """Dev-only identity gate. NEVER use in production — replace with real
    KYC/attestation verification (P4)."""

    def verify(self, agent: Agent) -> bool:
        return True


class AllowAllFraudFilter:
    """Dev-only per-request filter (P11). NEVER use in production — replace
    with real Sybil/anomaly detection on submitted requests."""

    def allow_intent(self, intent: Intent) -> bool:
        return True

    def allow_offer(self, offer: Offer) -> bool:
        return True


class LoggingNotifier:
    """Dev-only notifier: prints instead of pushing/webhooking."""

    def __init__(self) -> None:
        self.events: list[tuple[str, str, dict]] = []

    def notify(self, agent_id: str, event: str, payload: dict) -> None:
        self.events.append((agent_id, event, payload))


class AlwaysEscalateResolver:
    """Reference DisputeResolver: decides nothing, always escalates beyond
    the network. A legitimate minimal policy (docs/spec/05 §5) — real
    operators plug in their own adjudication rules here (Layer C)."""

    def resolve(self, dispute: Dispute, commitment: Commitment) -> Dispute:
        dispute.status = DisputeStatus.UNDER_REVIEW
        dispute.outcome = DisputeOutcome.ESCALATED
        return dispute
