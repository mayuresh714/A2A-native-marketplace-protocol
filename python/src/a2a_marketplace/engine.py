"""The neutral mechanism (Layer A).

The engine runs the machine and holds no policy of its own: it does not rank
(that is the operator's RankingPolicy, P10), it does not set price, it does
not decide dispute outcomes (that is the operator's DisputeResolver, Layer
C), and it does not know what a "ride" or a "restaurant" is (that is a
Category plugin). It only enforces the rules of the game:

    per-request fraud filter (P11)
      -> partition into DEMAND queue / SUPPLY queue (P11, P6 FIFO)
        -> solo-first match (P5)
          -> [on solo failure, after this intent's own wait timer expires]
             consumer-coalition attempt, demand-only (P1, P5, P12)
            -> STAGED match proposal, both sides notified (P11)
              -> both sides approve + funds captured into PLATFORM
                 CUSTODY -> Commitment formed (an AGREEMENT, not final) (P7, P8, P11)
                -> fulfillment WINDOW opens (P13); a dispute may be
                   raised by either side at any point in that window
                  -> no dispute: dual approval + evidence -> SETTLEMENT (P8)
                  -> dispute: escrow freezes; DisputeResolver decides (Layer C)

See docs/spec/01 Part B for the full lifecycle diagram this implements, and
docs/spec/05 for the dispute state machine specifically.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta

from .errors import (
    DisputeInProgressError,
    IdentityRejectedError,
    MandateViolationError,
    RequestRejectedError,
    UnknownCategoryError,
)
from .models import (
    Agent,
    Coalition,
    Commitment,
    CommitmentStatus,
    Dispute,
    DisputeOutcome,
    DisputeStatus,
    Escrow,
    EscrowState,
    Fulfillment,
    FulfillmentOutcome,
    Intent,
    Mandate,
    MatchProposal,
    Money,
    Offer,
    PriceRule,
    ProposalStatus,
    Settlement,
    Stance,
)
from .ports import (
    Category,
    Clock,
    DisputeResolver,
    EscrowProvider,
    IdentityVerifier,
    Notifier,
    RankingPolicy,
    RequestFraudFilter,
    Storage,
)


def _id() -> str:
    return str(uuid.uuid4())


class MarketplaceEngine:
    """Business-neutral marketplace core. Everything variable is injected."""

    def __init__(
        self,
        *,
        storage: Storage,
        clock: Clock,
        ranking: RankingPolicy,
        escrow: EscrowProvider,
        identity: IdentityVerifier,
        categories: dict[str, Category],
        fraud_filter: RequestFraudFilter,
        notifier: Notifier,
        dispute_resolver: DisputeResolver,
        mandates: dict[str, Mandate] | None = None,
        fee_bps: int = 200,  # thin protocol fee; 200 bps = 2% (docs/tdd/07)
        proposal_ttl_seconds: int = 900,
    ) -> None:
        self.storage = storage
        self.clock = clock
        self.ranking = ranking
        self.escrow = escrow
        self.identity = identity
        self.categories = categories
        self.fraud_filter = fraud_filter
        self.notifier = notifier
        self.dispute_resolver = dispute_resolver
        self.mandates = mandates if mandates is not None else {}
        self.fee_bps = fee_bps
        self.proposal_ttl_seconds = proposal_ttl_seconds
        self._commitments: dict[str, Commitment] = {}

    # -- onboarding -----------------------------------------------------------

    def register_agent(self, agent: Agent) -> None:
        """Fraud gate at entry (P4) — once, per agent."""
        if not self.identity.verify(agent):
            raise IdentityRejectedError(agent.agent_id)

    def register_mandate(self, mandate: Mandate) -> None:
        self.mandates[mandate.mandate_id] = mandate

    # -- submission -------------------------------------------------------------

    def submit_intent(self, intent: Intent) -> None:
        cat = self._category(intent.category_ref)
        cat.validate_intent(intent)
        if not self.fraud_filter.allow_intent(intent):  # P11: per-REQUEST filter
            raise RequestRejectedError(intent.intent_id)
        self.storage.add_intent(intent)

    def submit_offer(self, offer: Offer) -> None:
        cat = self._category(offer.category_ref)
        cat.validate_offer(offer)
        if not self.fraud_filter.allow_offer(offer):
            raise RequestRejectedError(offer.offer_id)
        self.storage.add_offer(offer)

    # -- matching (produces STAGED PROPOSALS, not commitments) ------------------

    def run_partition(self, category_ref: str, partition) -> list[MatchProposal]:
        """Process one partition's demand/supply queues, returning any newly
        staged match proposals (P11). A proposal is not yet a Commitment.

        Sharding means this runs independently per partition, with no
        cross-partition coordination — the basis for horizontal scale
        (docs/technical-deep-dive/01).
        """
        cat = self._category(category_ref)
        now = self.clock.now()
        proposals: list[MatchProposal] = []

        demand = self.storage.demand_queue(category_ref, partition)  # P11: demand queue
        for intent in demand:
            if intent.matched or intent.expiry < now:
                continue
            offers = [
                o
                for o in self.storage.supply_queue(category_ref, partition)  # P11: supply queue
                if o.capacity.remaining > 0 and o.hold_expires_at >= now
            ]
            serviceable = [o for o in offers if cat.satisfies(intent, o, now)]

            # P5: solo-first. An offer is solo-activatable only if this intent
            # alone meets its minimum fill.
            solo = [o for o in serviceable if intent.constraints.quantity >= o.capacity.min_fill]
            ranked = self.ranking.rank(intent, solo)
            if ranked:
                proposals.append(self._propose_solo(cat, intent, ranked[0], now))
                continue

            # P12: escalate to the collaboration queue only after THIS
            # intent's own wait timer has expired — not immediately.
            if intent.coalition_opt_in and now >= intent.collaboration_eligible_at():
                p = self._try_coalition(cat, intent, serviceable, demand, now)
                if p is not None:
                    proposals.append(p)
                    continue
            # otherwise it stays queued for a later tick

        return proposals

    # -- coalition formation (P1 demand-only, P5 on-failure, P12 time-boxed) ----

    def _try_coalition(
        self,
        cat: Category,
        seed: Intent,
        serviceable_offers: list[Offer],
        queue: list[Intent],
        now: datetime,
    ) -> MatchProposal | None:
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
                if not cat.compatible(candidate_group):
                    continue
                members.append(other)
                total_qty += other.constraints.quantity

            if total_qty < offer.capacity.min_fill or len(members) < 2:
                continue
            if not cat.compatible(members):
                continue

            member_prices = {m.intent_id: cat.price_for(m, offer) for m in members}
            total_price = self._sum(list(member_prices.values()))
            departure = self._offer_departure(cat, offer, members[0])
            coalition = Coalition(
                coalition_id=_id(),
                member_intent_refs=[m.intent_id for m in members],
                proposed_departure=departure,
                total_price=total_price,
                price_rule=PriceRule.ADDITIVE,
                stance=Stance.DEMAND,
            )
            return self._stage_proposal(
                offer=offer,
                demand_ref=coalition.coalition_id,
                demand_kind="coalition",
                demand_agents=[m.issuer_ref for m in members],
                members=members,
                member_prices=member_prices,
                total_price=total_price,
                departure=departure,
                quantity=total_qty,
                detail={"drops": [{"intent_ref": m.intent_id} for m in members]},
                mandate_refs=[m.mandate_ref for m in members],
                now=now,
            )
        return None

    # -- staging (P11: propose, notify, wait for dual approval + funds) --------

    def _propose_solo(self, cat: Category, intent: Intent, offer: Offer, now: datetime) -> MatchProposal:
        price = cat.price_for(intent, offer)
        departure = self._offer_departure(cat, offer, intent)
        return self._stage_proposal(
            offer=offer,
            demand_ref=intent.intent_id,
            demand_kind="intent",
            demand_agents=[intent.issuer_ref],
            members=[intent],
            member_prices={intent.intent_id: price},
            total_price=price,
            departure=departure,
            quantity=intent.constraints.quantity,
            detail={"drops": [{"intent_ref": intent.intent_id}]},
            mandate_refs=[intent.mandate_ref],
            now=now,
        )

    def _stage_proposal(
        self,
        *,
        offer: Offer,
        demand_ref: str,
        demand_kind: str,
        demand_agents: list[str],
        members: list[Intent],
        member_prices: dict[str, Money],
        total_price: Money,
        departure: datetime,
        quantity: int,
        detail: dict,
        mandate_refs: list[str],
        now: datetime,
    ) -> MatchProposal:
        # Hard mandate check happens now, not at approval time — an
        # over-budget match is never even proposed (P4/P8). Each member is
        # checked against their OWN share, never the group total.
        for m in members:
            self._check_mandate(m, member_prices[m.intent_id])

        proposal = MatchProposal(
            proposal_id=_id(),
            offer_ref=offer.offer_id,
            demand_ref=demand_ref,
            demand_kind=demand_kind,
            demand_agents=demand_agents,
            supply_agent=offer.issuer_ref,
            total_price=total_price,
            departure=departure,
            quantity=quantity,
            detail=detail,
            mandate_refs=mandate_refs,
            created_at=now,
            respond_by=now + timedelta(seconds=self.proposal_ttl_seconds),
        )

        # Reserve capacity optimistically so a second proposal can't also
        # claim it while this one awaits approval (docs/tdd/01 §3).
        offer.capacity.remaining -= quantity
        for m in members:
            m.matched = True

        # Auto-approval: a posted offer IS the provider's blanket approval
        # unless the category/operator requires explicit per-match consent.
        if not offer.requires_explicit_approval:
            proposal.provider_approved = True
        # A demand-side agent auto-approves only if EVERY member's mandate
        # allows auto-commit within scope (already budget-checked above).
        if all(self._auto_commits(m) for m in members):
            proposal.consumer_approved = True

        self.notifier.notify(offer.issuer_ref, "match_proposed", {"proposal_id": proposal.proposal_id})
        for agent_id in demand_agents:
            self.notifier.notify(agent_id, "match_proposed", {"proposal_id": proposal.proposal_id})

        self.storage.save_proposal(proposal)

        if proposal.consumer_approved and proposal.provider_approved:
            self._finalize_proposal(proposal, offer)
        return proposal

    def approve_proposal(
        self, proposal: MatchProposal, side: str, approved: bool = True
    ) -> Commitment | None:
        """Explicit approval call for a side that didn't auto-approve. Once
        BOTH sides have approved, funds are captured and the Commitment
        forms — this is the P11 "agreement, not final step" boundary."""
        if side not in ("consumer", "provider"):
            raise ValueError("side must be 'consumer' or 'provider'")
        if proposal.status != ProposalStatus.PROPOSED:
            return None

        if not approved:
            proposal.status = ProposalStatus.DECLINED
            self._release_reservation(proposal)
            return None

        if side == "consumer":
            proposal.consumer_approved = True
        else:
            proposal.provider_approved = True
        self.storage.save_proposal(proposal)

        if proposal.consumer_approved and proposal.provider_approved:
            offer = self.storage.get_offer(proposal.offer_ref)
            if offer is None:
                raise UnknownCategoryError("offer not found for proposal")
            return self._finalize_proposal(proposal, offer)
        return None

    def expire_proposal(self, proposal: MatchProposal, now: datetime | None = None) -> None:
        now = now or self.clock.now()
        if proposal.status == ProposalStatus.PROPOSED and now >= proposal.respond_by:
            proposal.status = ProposalStatus.EXPIRED
            self._release_reservation(proposal)

    def _release_reservation(self, proposal: MatchProposal) -> None:
        offer = self.storage.get_offer(proposal.offer_ref)
        if offer is not None:
            offer.capacity.remaining += proposal.quantity
        # Unmark the member intents so they re-enter the demand queue.
        for drop in proposal.detail.get("drops", []):
            intent = self.storage.get_intent(drop["intent_ref"])
            if intent is not None:
                intent.matched = False

    def _finalize_proposal(self, proposal: MatchProposal, offer: Offer) -> Commitment:
        escrow = Escrow(amount=proposal.total_price, provider_stake=offer.provider_stake)
        commitment = Commitment(
            commitment_id=_id(),
            offer_ref=offer.offer_id,
            demand_ref=proposal.demand_ref,
            demand_kind=proposal.demand_kind,
            supply_agent=proposal.supply_agent,
            demand_agents=proposal.demand_agents,
            total_price=proposal.total_price,
            departure=proposal.departure,
            escrow=escrow,
            mandate_refs=proposal.mandate_refs,
            created_at=self.clock.now(),
            status=CommitmentStatus.HELD,
            detail=proposal.detail,
        )
        if not self.escrow.hold(commitment):
            raise MandateViolationError("escrow hold failed: funds not captured")
        commitment.escrow.state = EscrowState.HELD
        commitment.status = CommitmentStatus.CONFIRMED  # P11: agreement, not final
        self.storage.save_commitment(commitment)
        self._commitments[commitment.commitment_id] = commitment
        proposal.status = ProposalStatus.APPROVED
        self.storage.save_proposal(proposal)
        return commitment

    # -- fulfillment window + disputes (P8, P13) --------------------------------

    def raise_dispute(self, commitment: Commitment, raised_by: str, reason_code: str) -> Dispute:
        """Either party may raise a dispute at any point before settlement
        (docs/spec/05). Freezes escrow unconditionally — no money moves
        until resolved."""
        if commitment.escrow.state not in (EscrowState.HELD, EscrowState.AUTHORIZED):
            raise DisputeInProgressError(
                f"cannot dispute a commitment whose escrow is already {commitment.escrow.state.value}"
            )
        dispute = Dispute(
            dispute_id=_id(),
            commitment_ref=commitment.commitment_id,
            raised_by=raised_by,
            reason_code=reason_code,
            raised_at=self.clock.now(),
        )
        commitment.escrow.state = EscrowState.DISPUTED  # unconditional freeze
        self.storage.save_dispute(dispute)
        return dispute

    def resolve_dispute(self, dispute: Dispute, commitment: Commitment) -> Dispute:
        """Hands off to the operator's DisputeResolver (Layer C). The engine
        only applies whatever payout the resolver decided, and only from the
        protocol's closed outcome vocabulary (docs/spec/05 §5)."""
        resolved = self.dispute_resolver.resolve(dispute, commitment)
        self.storage.save_dispute(resolved)
        if resolved.outcome is not None and resolved.payouts:
            self.escrow.payout(commitment, resolved.payouts)
            if resolved.outcome == DisputeOutcome.FULL_REFUND:
                commitment.escrow.state = EscrowState.REFUNDED
            else:  # FULL_RELEASE or PARTIAL both move funds out
                commitment.escrow.state = EscrowState.RELEASED
            resolved.status = DisputeStatus.RESOLVED
            resolved.resolved_at = self.clock.now()
            self.storage.save_dispute(resolved)
        # ESCALATED (or no payout decided yet): stays DISPUTED, frozen.
        return resolved

    def fulfill(
        self,
        commitment: Commitment,
        *,
        consumer_approved: bool,
        provider_approved: bool,
        evidence: dict,
    ) -> tuple[Fulfillment, Settlement | None]:
        """Record the three P8 gates. Money moves only if all three pass AND
        no dispute is open on this commitment."""
        if commitment.escrow.state == EscrowState.DISPUTED:
            raise DisputeInProgressError(commitment.commitment_id)

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
        payouts = {commitment.supply_agent: net, "platform": fee}
        if commitment.escrow.provider_stake is not None:
            payouts[commitment.supply_agent] = payouts[commitment.supply_agent] + commitment.escrow.provider_stake
        self.escrow.payout(commitment, payouts)
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

    def _auto_commits(self, intent: Intent) -> bool:
        mandate = self.mandates.get(intent.mandate_ref)
        if mandate is None:
            return False
        from .models import AutonomyLevel

        return mandate.autonomy_level == AutonomyLevel.AUTO_COMMIT_WITHIN_SCOPE

    def _check_mandate(self, intent: Intent, price: Money) -> None:
        mandate = self.mandates.get(intent.mandate_ref)
        if mandate is None:
            return  # no mandate registered -> engine can't enforce; operator's call
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
