"""The neutral mechanism (Layer A).

The engine runs the machine and holds no policy of its own: it does not rank
(that is the operator's RankingPolicy, P10), it does not set price, and it
does not know what a "ride" or a "restaurant" is (that is a Category plugin).
It only enforces the rules of the game:

    partition + FIFO queue (P6)
      -> solo-first match (P5)
        -> consumer-coalition on failure (P1 demand-only, P5)
          -> commitment + escrow (P7, P8)
            -> fulfillment: dual approval + evidence (P8)
              -> settlement (thin fee)

See docs/spec/01 Part B for the lifecycle this implements.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from .errors import (
    IdentityRejectedError,
    MandateViolationError,
    UnknownCategoryError,
)
from .models import (
    Agent,
    Coalition,
    Commitment,
    CommitmentStatus,
    Escrow,
    EscrowState,
    Fulfillment,
    FulfillmentOutcome,
    Intent,
    Mandate,
    Money,
    Offer,
    PriceRule,
    Settlement,
    Stance,
)
from .ports import (
    Category,
    Clock,
    EscrowProvider,
    IdentityVerifier,
    RankingPolicy,
    Storage,
)


def _id() -> str:
    return str(uuid.uuid4())


class MarketplaceEngine:
    """Business-neutral marketplace core.

    Everything variable is injected. Nothing in here favors any operator or
    vertical; that is the whole point of an open protocol implementation.
    """

    def __init__(
        self,
        *,
        storage: Storage,
        clock: Clock,
        ranking: RankingPolicy,
        escrow: EscrowProvider,
        identity: IdentityVerifier,
        categories: dict[str, Category],
        mandates: dict[str, Mandate] | None = None,
        fee_bps: int = 200,  # thin protocol fee; 200 bps = 2% (docs/tdd/07)
    ) -> None:
        self.storage = storage
        self.clock = clock
        self.ranking = ranking
        self.escrow = escrow
        self.identity = identity
        self.categories = categories
        self.mandates = mandates if mandates is not None else {}
        self.fee_bps = fee_bps

    # -- onboarding -----------------------------------------------------------

    def register_agent(self, agent: Agent) -> None:
        """Fraud gate at entry (P4)."""
        if not self.identity.verify(agent):
            raise IdentityRejectedError(agent.agent_id)

    def register_mandate(self, mandate: Mandate) -> None:
        self.mandates[mandate.mandate_id] = mandate

    # -- submission -----------------------------------------------------------

    def submit_intent(self, intent: Intent) -> None:
        cat = self._category(intent.category_ref)
        cat.validate_intent(intent)
        self.storage.add_intent(intent)

    def submit_offer(self, offer: Offer) -> None:
        cat = self._category(offer.category_ref)
        cat.validate_offer(offer)
        self.storage.add_offer(offer)

    # -- matching (the core loop) --------------------------------------------

    def run_partition(self, category_ref: str, partition) -> list[Commitment]:
        """Process one partition's FIFO queue, returning the commitments formed.

        Sharding means this runs independently per partition, with no
        cross-partition coordination — the basis for horizontal scale
        (docs/technical-deep-dive/01).
        """
        cat = self._category(category_ref)
        now = self.clock.now()
        committed: list[Commitment] = []

        queue = self.storage.queued_intents(category_ref, partition)
        for intent in queue:
            if intent.matched or intent.expiry < now:
                continue
            offers = [
                o
                for o in self.storage.offers_in_partition(category_ref, partition)
                if o.capacity.remaining > 0 and o.hold_expires_at >= now
            ]
            serviceable = [o for o in offers if cat.satisfies(intent, o, now)]

            # P5: solo-first. An offer is solo-activatable only if this intent
            # alone meets its minimum fill.
            solo = [o for o in serviceable if intent.constraints.quantity >= o.capacity.min_fill]
            ranked = self.ranking.rank(intent, solo)
            if ranked:
                committed.append(self._commit_solo(cat, intent, ranked[0], now))
                continue

            # P5 + P1: collaborate only on failure, demand side only.
            if intent.coalition_opt_in:
                c = self._try_coalition(cat, intent, serviceable, queue, now)
                if c is not None:
                    committed.append(c)
                    continue
            # otherwise the intent stays queued for a later tick

        return committed

    # -- coalition formation (P1 demand-only, P5 on-failure) ------------------

    def _try_coalition(
        self,
        cat: Category,
        seed: Intent,
        serviceable_offers: list[Offer],
        queue: list[Intent],
        now: datetime,
    ) -> Commitment | None:
        for offer in serviceable_offers:
            members: list[Intent] = [seed]
            total_qty = seed.constraints.quantity
            for other in queue:
                if total_qty >= offer.capacity.min_fill:
                    break
                if other is seed or other.matched or not other.coalition_opt_in:
                    continue
                if total_qty + other.constraints.quantity > offer.capacity.remaining:
                    continue
                if not cat.satisfies(other, offer, now):
                    continue
                candidate_group = members + [other]
                if not cat.compatible(candidate_group):  # keep the group compatible
                    continue
                members.append(other)
                total_qty += other.constraints.quantity

            if total_qty < offer.capacity.min_fill or len(members) < 2:
                continue
            if not cat.compatible(members):
                continue

            total_price = self._sum([cat.price_for(m, offer) for m in members])
            coalition = Coalition(
                coalition_id=_id(),
                member_intent_refs=[m.intent_id for m in members],
                proposed_departure=offer.hold_expires_at,  # placeholder; refined below
                total_price=total_price,
                price_rule=PriceRule.ADDITIVE,
                stance=Stance.DEMAND,
            )
            # departure = the offer's own departure, which satisfies() already
            # proved lies inside every member's window.
            departure = self._offer_departure(cat, offer, members[0])
            coalition.proposed_departure = departure
            return self._commit_coalition(cat, coalition, members, offer, departure, now)
        return None

    # -- commitment + escrow (P7, P8) -----------------------------------------

    def _commit_solo(self, cat: Category, intent: Intent, offer: Offer, now: datetime) -> Commitment:
        price = cat.price_for(intent, offer)
        self._check_mandate(intent, price)
        departure = self._offer_departure(cat, offer, intent)
        commitment = Commitment(
            commitment_id=_id(),
            offer_ref=offer.offer_id,
            demand_ref=intent.intent_id,
            demand_kind="intent",
            supply_agent=offer.issuer_ref,
            demand_agents=[intent.issuer_ref],
            total_price=price,
            departure=departure,
            escrow=Escrow(amount=price),
            mandate_refs=[intent.mandate_ref],
            created_at=now,
            detail={"drops": [{"intent_ref": intent.intent_id}]},
        )
        self._finalize_commitment(commitment, offer, intent.constraints.quantity, [intent])
        return commitment

    def _commit_coalition(
        self,
        cat: Category,
        coalition: Coalition,
        members: list[Intent],
        offer: Offer,
        departure: datetime,
        now: datetime,
    ) -> Commitment:
        for m in members:
            self._check_mandate(m, cat.price_for(m, offer))
        qty = sum(m.constraints.quantity for m in members)
        commitment = Commitment(
            commitment_id=_id(),
            offer_ref=offer.offer_id,
            demand_ref=coalition.coalition_id,
            demand_kind="coalition",
            supply_agent=offer.issuer_ref,
            demand_agents=[m.issuer_ref for m in members],
            total_price=coalition.total_price,
            departure=departure,
            escrow=Escrow(amount=coalition.total_price),
            mandate_refs=[m.mandate_ref for m in members],
            created_at=now,
            detail={"drops": [{"intent_ref": m.intent_id} for m in members]},
        )
        self._finalize_commitment(commitment, offer, qty, members)
        return commitment

    def _finalize_commitment(
        self, commitment: Commitment, offer: Offer, qty: int, members: list[Intent]
    ) -> None:
        if not self.escrow.hold(commitment):
            raise MandateViolationError("escrow hold failed")
        commitment.escrow.state = EscrowState.HELD
        commitment.status = CommitmentStatus.CONFIRMED
        offer.capacity.remaining -= qty  # optimistic decrement (docs/tdd/01 §3)
        for m in members:
            m.matched = True
        self.storage.save_commitment(commitment)

    # -- fulfillment + settlement (P8) ----------------------------------------

    def fulfill(
        self,
        commitment: Commitment,
        *,
        consumer_approved: bool,
        provider_approved: bool,
        evidence: dict,
    ) -> tuple[Fulfillment, Settlement | None]:
        """Record the three P8 gates. Money moves only if all three pass."""
        cat = self._category_of_commitment(commitment)
        verified = cat.verify_evidence(commitment, evidence)
        all_pass = consumer_approved and provider_approved and verified
        fulfillment = Fulfillment(
            fulfillment_id=_id(),
            commitment_ref=commitment.commitment_id,
            consumer_approved=consumer_approved,
            provider_approved=provider_approved,
            platform_verified=verified,
            outcome=FulfillmentOutcome.COMPLETED if all_pass else FulfillmentOutcome.DISPUTED,
            evidence=evidence,
        )
        self.storage.save_fulfillment(fulfillment)

        if not all_pass:
            commitment.escrow.state = EscrowState.DISPUTED
            return fulfillment, None

        settlement = self._settle(commitment, fulfillment)
        return fulfillment, settlement

    def _settle(self, commitment: Commitment, fulfillment: Fulfillment) -> Settlement:
        gross = commitment.escrow.amount
        fee = gross.bps(self.fee_bps)
        net = gross.minus(fee)
        self.escrow.release(commitment, net, fee)
        commitment.escrow.state = EscrowState.RELEASED
        settlement = Settlement(
            settlement_id=_id(),
            commitment_ref=commitment.commitment_id,
            fulfillment_ref=fulfillment.fulfillment_id,
            gross=gross,
            protocol_fee=fee,
            net_to_provider=net,
            released_at=self.clock.now(),
        )
        self.storage.save_settlement(settlement)
        return settlement

    # -- helpers --------------------------------------------------------------

    def _check_mandate(self, intent: Intent, price: Money) -> None:
        mandate = self.mandates.get(intent.mandate_ref)
        if mandate is None:
            return  # no mandate registered → engine can't enforce; operator's call
        # Hard, code-level budget check — never delegated to an LLM (P4/tdd06).
        if not (price <= mandate.budget_ceiling):
            raise MandateViolationError(
                f"price {price.amount_minor} exceeds mandate ceiling "
                f"{mandate.budget_ceiling.amount_minor}"
            )

    @staticmethod
    def _sum(amounts: list[Money]) -> Money:
        total = amounts[0]
        for a in amounts[1:]:
            total = total + a
        return total

    def _offer_departure(self, cat: Category, offer: Offer, intent: Intent) -> datetime:
        # Categories may expose a departure; fall back to the intent's earliest.
        dep = offer.category_ext.get("departure")
        if isinstance(dep, datetime):
            return dep
        return intent.constraints.time_window.earliest

    def _category(self, category_ref: str) -> Category:
        try:
            return self.categories[category_ref]
        except KeyError as e:
            raise UnknownCategoryError(category_ref) from e

    def _category_of_commitment(self, commitment: Commitment) -> Category:
        offer = self.storage.get_offer(commitment.offer_ref)
        if offer is None:
            raise UnknownCategoryError("offer not found for commitment")
        return self._category(offer.category_ref)
