"""End-to-end and principle-enforcement tests."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from a2a_marketplace import MarketplaceEngine, IntercityTravelCategory
from a2a_marketplace.adapters import (
    AllowAllFraudFilter,
    AllowAllIdentity,
    AlwaysEscalateResolver,
    FixedClock,
    InMemoryStorage,
    LoggingNotifier,
    PriceAscRanking,
    SimEscrow,
)
from a2a_marketplace.errors import DisputeInProgressError, MandateViolationError
from a2a_marketplace.models import (
    AutonomyLevel,
    Capacity,
    Coalition,
    Constraints,
    DisputeStatus,
    EscrowState,
    Intent,
    Mandate,
    Money,
    Offer,
    ProposalStatus,
    Stance,
    TimeWindow,
    partition_of,
)

IST = timezone(timedelta(hours=5, minutes=30))


def rupees(n: int) -> Money:
    return Money(n * 100, "INR")


def make_engine(fee_bps: int = 200, proposal_ttl_seconds: int = 900) -> MarketplaceEngine:
    cat = IntercityTravelCategory()
    return MarketplaceEngine(
        storage=InMemoryStorage(),
        clock=FixedClock(datetime(2026, 7, 17, 9, 0, tzinfo=IST)),
        ranking=PriceAscRanking(),
        escrow=SimEscrow(),
        identity=AllowAllIdentity(),
        categories={cat.id: cat},
        fraud_filter=AllowAllFraudFilter(),
        notifier=LoggingNotifier(),
        dispute_resolver=AlwaysEscalateResolver(),
        fee_bps=fee_bps,
        proposal_ttl_seconds=proposal_ttl_seconds,
    )


CORRIDOR = {"source_region": "Pune", "destination_region": "Kolhapur",
            "start_time_bucket": "2026-07-18T15:00/17:00+05:30"}
DEP = datetime(2026, 7, 18, 15, 30, tzinfo=IST)
WINDOW = TimeWindow(datetime(2026, 7, 18, 14, 30, tzinfo=IST),
                    datetime(2026, 7, 18, 17, 0, tzinfo=IST))
T0 = datetime(2026, 7, 17, 9, 0, tzinfo=IST)


def _offer(min_fill: int, seats: int = 3, offer_id: str = "offer-1",
          requires_explicit_approval: bool = False) -> Offer:
    return Offer(
        offer_id=offer_id, issuer_ref="did:web:d:1", category_ref="intercity_travel",
        grouping_keys=CORRIDOR, capacity=Capacity("seat", seats, min_fill=min_fill),
        price=rupees(550), hold_expires_at=datetime(2026, 7, 17, 20, 0, tzinfo=IST),
        created_at=T0, requires_explicit_approval=requires_explicit_approval,
        category_ext={"departure": DEP, "route": [
            {"stop": "Pune", "eta": DEP},
            {"stop": "Satara", "eta": DEP + timedelta(hours=1), "price_per_seat": rupees(380)},
            {"stop": "Vadgaon", "eta": DEP + timedelta(hours=2), "price_per_seat": rupees(430)},
            {"stop": "Ichalkaranji", "eta": DEP + timedelta(hours=3), "price_per_seat": rupees(520)},
        ]},
    )


def _intent(
    name: str, drop: str, budget: int = 600, i: int = 0,
    autonomy: AutonomyLevel = AutonomyLevel.AUTO_COMMIT_WITHIN_SCOPE,
    solo_wait_seconds: int = 0, coalition_opt_in: bool = True,
) -> Intent:
    return Intent(
        intent_id=f"intent-{name}", issuer_ref=f"did:web:r:{name}",
        category_ref="intercity_travel", grouping_keys=CORRIDOR,
        constraints=Constraints(WINDOW, rupees(budget), 1),
        mandate_ref=f"m-{name}", created_at=T0 + timedelta(seconds=i),
        expiry=datetime(2026, 7, 18, 14, 0, tzinfo=IST),
        preferences={"drop_stop": drop}, coalition_opt_in=coalition_opt_in,
        solo_wait_seconds=solo_wait_seconds,
    )


def _register_riders(engine, names, budget=1000, autonomy=AutonomyLevel.AUTO_COMMIT_WITHIN_SCOPE):
    for n in names:
        engine.register_mandate(Mandate(f"m-{n}", f"r-{n}", f"did:web:r:{n}",
                                        "intercity_travel", rupees(budget), autonomy_level=autonomy))


def test_solo_match_auto_approves_and_forms_commitment():
    """Both sides auto-commit -> the proposal is finalized inside run_partition."""
    engine = make_engine()
    _register_riders(engine, ["a"])
    engine.submit_offer(_offer(min_fill=1))
    engine.submit_intent(_intent("a", "Satara"))
    proposals = engine.run_partition("intercity_travel", partition_of(CORRIDOR))
    assert len(proposals) == 1
    assert proposals[0].status == ProposalStatus.APPROVED
    commitment = next(iter(engine.storage.commitments.values()))
    assert commitment.demand_kind == "intent"
    assert commitment.status.value == "confirmed"


def test_match_is_staged_not_instant_when_consumer_must_confirm():
    """P11: a match creates a PROPOSAL first; it isn't a Commitment until
    both sides explicitly approve."""
    engine = make_engine()
    _register_riders(engine, ["a"], autonomy=AutonomyLevel.REQUIRE_CONFIRMATION)
    engine.submit_offer(_offer(min_fill=1))
    engine.submit_intent(_intent("a", "Satara"))
    proposals = engine.run_partition("intercity_travel", partition_of(CORRIDOR))
    proposal = proposals[0]
    assert proposal.status == ProposalStatus.PROPOSED
    assert proposal.provider_approved is True  # posting the offer was blanket approval
    assert proposal.consumer_approved is None  # rider must explicitly confirm
    assert len(engine.storage.commitments) == 0  # no Commitment yet

    commitment = engine.approve_proposal(proposal, side="consumer", approved=True)
    assert commitment is not None
    assert commitment.status.value == "confirmed"
    assert commitment.escrow.state == EscrowState.HELD


def test_explicit_provider_approval_required_when_offer_demands_it():
    engine = make_engine()
    _register_riders(engine, ["a"])
    engine.submit_offer(_offer(min_fill=1, requires_explicit_approval=True))
    engine.submit_intent(_intent("a", "Satara"))
    proposal = engine.run_partition("intercity_travel", partition_of(CORRIDOR))[0]
    assert proposal.provider_approved is None
    assert proposal.consumer_approved is True  # rider auto-commits
    assert engine.approve_proposal(proposal, side="provider", approved=True) is not None


def test_declining_a_proposal_releases_reserved_capacity():
    engine = make_engine()
    _register_riders(engine, ["a"], autonomy=AutonomyLevel.REQUIRE_CONFIRMATION)
    offer = _offer(min_fill=1, seats=1)
    engine.submit_offer(offer)
    engine.submit_intent(_intent("a", "Satara"))
    proposal = engine.run_partition("intercity_travel", partition_of(CORRIDOR))[0]
    assert offer.capacity.remaining == 0  # reserved while proposal is pending

    result = engine.approve_proposal(proposal, side="consumer", approved=False)
    assert result is None
    assert proposal.status == ProposalStatus.DECLINED
    assert offer.capacity.remaining == 1  # released back
    assert engine.storage.get_intent("intent-a").matched is False  # back in the demand queue


def test_coalition_forms_only_after_solo_wait_timer_expires():
    """P12: escalation to the collaboration queue is time-boxed, not immediate."""
    engine = make_engine()
    _register_riders(engine, ["a", "b", "c"])
    engine.submit_offer(_offer(min_fill=3))
    for k, (n, drop) in enumerate([("a", "Satara"), ("b", "Vadgaon"), ("c", "Ichalkaranji")]):
        engine.submit_intent(_intent(n, drop, i=k, solo_wait_seconds=300))  # 5 min wait

    # Still within the wait window: no solo match possible (offer needs 3),
    # and coalition escalation hasn't fired yet.
    proposals = engine.run_partition("intercity_travel", partition_of(CORRIDOR))
    assert proposals == []

    # Advance past every intent's wait timer.
    engine.clock.set(T0 + timedelta(seconds=301))
    proposals = engine.run_partition("intercity_travel", partition_of(CORRIDOR))
    assert len(proposals) == 1
    assert proposals[0].demand_kind == "coalition"
    assert len(proposals[0].demand_agents) == 3
    assert proposals[0].total_price == rupees(380 + 430 + 520)


def test_coalition_member_mandate_checked_against_own_share_not_group_total():
    """A member's mandate must be checked against their own price, not the
    coalition's combined total (a real correctness requirement, not just
    'conservative')."""
    engine = make_engine()
    _register_riders(engine, ["a", "b"], budget=1000)
    # rider c's ceiling covers their own Rs.520 fare but not the Rs.1330 group total
    _register_riders(engine, ["c"], budget=550)
    engine.submit_offer(_offer(min_fill=3))
    for k, (n, drop) in enumerate([("a", "Satara"), ("b", "Vadgaon"), ("c", "Ichalkaranji")]):
        engine.submit_intent(_intent(n, drop, i=k))
    proposals = engine.run_partition("intercity_travel", partition_of(CORRIDOR))
    assert len(proposals) == 1  # would have raised MandateViolationError if checked wrong


def test_settlement_requires_all_three_gates():
    engine = make_engine(fee_bps=200)
    _register_riders(engine, ["a", "b", "c"])
    engine.submit_offer(_offer(min_fill=3))
    for k, (n, drop) in enumerate([("a", "Satara"), ("b", "Vadgaon"), ("c", "Ichalkaranji")]):
        engine.submit_intent(_intent(n, drop, i=k))
    engine.run_partition("intercity_travel", partition_of(CORRIDOR))
    commitment = next(iter(engine.storage.commitments.values()))
    assert commitment is not None

    evidence = {"dropoffs": [{"intent_ref": f"intent-{n}", "confirmed_at": DEP}
                            for n in ("a", "b", "c")]}

    f1, s1 = engine.fulfill(commitment, consumer_approved=True,
                            provider_approved=False, evidence=evidence)
    assert s1 is None
    assert commitment.escrow.state == EscrowState.DISPUTED

    commitment.escrow.state = EscrowState.HELD  # reset for the positive case
    f2, s2 = engine.fulfill(commitment, consumer_approved=True,
                            provider_approved=True, evidence=evidence)
    assert s2 is not None
    assert s2.gross == rupees(1330)
    assert s2.protocol_fee == Money(133000 * 200 // 10000, "INR")
    assert s2.net_to_provider == s2.gross.minus(s2.protocol_fee)
    assert commitment.escrow.state == EscrowState.RELEASED


def test_no_evidence_blocks_settlement():
    engine = make_engine()
    _register_riders(engine, ["a", "b", "c"])
    engine.submit_offer(_offer(min_fill=3))
    for k, (n, drop) in enumerate([("a", "Satara"), ("b", "Vadgaon"), ("c", "Ichalkaranji")]):
        engine.submit_intent(_intent(n, drop, i=k))
    engine.run_partition("intercity_travel", partition_of(CORRIDOR))
    commitment = next(iter(engine.storage.commitments.values()))
    _, settlement = engine.fulfill(commitment, consumer_approved=True,
                                   provider_approved=True, evidence={})
    assert settlement is None


def test_dispute_freezes_escrow_and_blocks_fulfill():
    """P13: a dispute can be raised at any point before settlement; the
    freeze is unconditional and fulfill() must refuse while it's open."""
    engine = make_engine()
    _register_riders(engine, ["a"])
    engine.submit_offer(_offer(min_fill=1))
    engine.submit_intent(_intent("a", "Satara"))
    engine.run_partition("intercity_travel", partition_of(CORRIDOR))
    commitment = next(iter(engine.storage.commitments.values()))

    dispute = engine.raise_dispute(commitment, raised_by="consumer", reason_code="timing")
    assert commitment.escrow.state == EscrowState.DISPUTED
    assert dispute.status == DisputeStatus.OPEN

    with pytest.raises(DisputeInProgressError):
        engine.fulfill(commitment, consumer_approved=True, provider_approved=True, evidence={})


def test_dispute_resolution_is_delegated_to_operator_policy():
    """The engine never decides dispute outcomes itself (Layer C); the
    reference AlwaysEscalateResolver leaves escrow frozen and pending."""
    engine = make_engine()
    _register_riders(engine, ["a"])
    engine.submit_offer(_offer(min_fill=1))
    engine.submit_intent(_intent("a", "Satara"))
    engine.run_partition("intercity_travel", partition_of(CORRIDOR))
    commitment = next(iter(engine.storage.commitments.values()))
    dispute = engine.raise_dispute(commitment, raised_by="provider", reason_code="no_show")

    resolved = engine.resolve_dispute(dispute, commitment)
    assert resolved.outcome.value == "escalated"
    assert resolved.status == DisputeStatus.UNDER_REVIEW  # not RESOLVED — no payout happened
    assert commitment.escrow.state == EscrowState.DISPUTED  # still frozen


def test_supply_coalition_is_forbidden_by_construction():
    """P1: provider-side coalitions must be impossible to construct."""
    with pytest.raises(ValueError):
        Coalition(coalition_id="x", member_intent_refs=["a", "b"],
                  proposed_departure=DEP, total_price=rupees(100), stance=Stance.SUPPLY)


def test_mandate_ceiling_is_enforced_in_code():
    """P4/P8: an over-budget commitment is blocked by the engine, not trusted."""
    engine = make_engine()
    engine.register_mandate(Mandate("m-a", "r-a", "did:web:r:a", "intercity_travel", rupees(400)))
    engine.submit_offer(_offer(min_fill=1))
    engine.submit_intent(_intent("a", "Ichalkaranji", budget=600))  # constraint passes (520<600)
    with pytest.raises(MandateViolationError):
        engine.run_partition("intercity_travel", partition_of(CORRIDOR))


def test_per_request_fraud_filter_rejects_before_queue_entry():
    from a2a_marketplace.errors import RequestRejectedError

    class RejectEverything:
        def allow_intent(self, intent):
            return False

        def allow_offer(self, offer):
            return True

    engine = make_engine()
    engine.fraud_filter = RejectEverything()
    engine.register_mandate(Mandate("m-a", "r-a", "did:web:r:a", "intercity_travel", rupees(1000)))
    with pytest.raises(RequestRejectedError):
        engine.submit_intent(_intent("a", "Satara"))
