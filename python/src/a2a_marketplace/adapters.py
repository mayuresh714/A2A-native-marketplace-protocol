"""Reference adapters: minimal in-memory implementations of every port.

These make the library run out of the box for development, testing, and
simulation. A production operator replaces each with their own infra
(Postgres/Redis storage, a real payment rail, real KYC) — the engine is
unchanged. Everything here is intentionally simple, not performant.
"""
from __future__ import annotations

from datetime import datetime, timezone

from .models import Agent, Commitment, Fulfillment, Intent, Money, Offer, Settlement
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


class InMemoryStorage:
    def __init__(self) -> None:
        self._intents: dict[str, Intent] = {}
        self._offers: dict[str, Offer] = {}
        self.commitments: dict[str, Commitment] = {}
        self.fulfillments: dict[str, Fulfillment] = {}
        self.settlements: dict[str, Settlement] = {}

    def add_intent(self, intent: Intent) -> None:
        self._intents[intent.intent_id] = intent

    def add_offer(self, offer: Offer) -> None:
        self._offers[offer.offer_id] = offer

    def get_offer(self, offer_id: str) -> Offer | None:
        return self._offers.get(offer_id)

    def queued_intents(self, category_ref: str, partition: Partition) -> list[Intent]:
        items = [
            i
            for i in self._intents.values()
            if i.category_ref == category_ref and i.partition == partition and not i.matched
        ]
        # FIFO: earliest created first (P6).
        return sorted(items, key=lambda i: i.created_at)

    def offers_in_partition(self, category_ref: str, partition: Partition) -> list[Offer]:
        return [
            o
            for o in self._offers.values()
            if o.category_ref == category_ref and o.partition == partition
        ]

    def save_commitment(self, commitment: Commitment) -> None:
        self.commitments[commitment.commitment_id] = commitment

    def save_fulfillment(self, fulfillment: Fulfillment) -> None:
        self.fulfillments[fulfillment.fulfillment_id] = fulfillment

    def save_settlement(self, settlement: Settlement) -> None:
        self.settlements[settlement.settlement_id] = settlement


class PriceAscRanking:
    """A trivial, neutral default: cheapest first. It exists only so the
    library runs unconfigured. Real operators inject their own RankingPolicy
    (by ETA, quality, strategy, ...) — ranking is theirs, not the protocol's
    (P10)."""

    def rank(self, intent: Intent, candidates: list[Offer]) -> list[Offer]:
        return sorted(candidates, key=lambda o: o.price.amount_minor)


class SimEscrow:
    """Simulated escrow: tracks held/released/refunded totals, no real money."""

    def __init__(self) -> None:
        self.held: dict[str, Money] = {}
        self.released: dict[str, tuple[Money, Money]] = {}  # net, fee
        self.refunded: dict[str, Money] = {}

    def hold(self, commitment: Commitment) -> bool:
        self.held[commitment.commitment_id] = commitment.escrow.amount
        return True

    def release(self, commitment: Commitment, net_to_provider: Money, fee: Money) -> None:
        self.held.pop(commitment.commitment_id, None)
        self.released[commitment.commitment_id] = (net_to_provider, fee)

    def refund(self, commitment: Commitment) -> None:
        amount = self.held.pop(commitment.commitment_id, None)
        if amount is not None:
            self.refunded[commitment.commitment_id] = amount


class AllowAllIdentity:
    """Dev-only identity gate. NEVER use in production — replace with real
    KYC/attestation verification (P4)."""

    def verify(self, agent: Agent) -> bool:
        return True
