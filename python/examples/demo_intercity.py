"""End-to-end demo: the Pune–Kolhapur coalition scenario from docs/design.md §5,
now showing the full staged lifecycle from docs/spec/01 Part B (P11-P13):
fraud-filtered submission -> solo match attempt -> TTL-gated escalation to
coalition -> STAGED proposal (not yet binding) -> explicit dual approval +
funds captured -> Commitment ("agreement, not final") -> fulfillment window
-> dual approval + evidence -> settlement. Plus a mid-window dispute example.

Run it::

    cd python && python examples/demo_intercity.py
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

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
from a2a_marketplace.models import (
    Agent,
    AutonomyLevel,
    Capacity,
    Constraints,
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
INR = "INR"


def rupees(n: int) -> Money:
    return Money(n * 100, INR)  # n rupees -> paise


def main() -> None:
    now = datetime(2026, 7, 17, 9, 0, tzinfo=IST)
    clock = FixedClock(now)
    cat = IntercityTravelCategory()
    notifier = LoggingNotifier()
    engine = MarketplaceEngine(
        storage=InMemoryStorage(),
        clock=clock,
        ranking=PriceAscRanking(),
        escrow=SimEscrow(),
        identity=AllowAllIdentity(),
        categories={cat.id: cat},
        fraud_filter=AllowAllFraudFilter(),
        notifier=notifier,
        dispute_resolver=AlwaysEscalateResolver(),
        fee_bps=200,  # 2%
        proposal_ttl_seconds=900,
    )

    corridor = {"source_region": "Pune", "destination_region": "Kolhapur",
                "start_time_bucket": "2026-07-18T15:00/17:00+05:30"}
    departure = datetime(2026, 7, 18, 15, 30, tzinfo=IST)
    window = TimeWindow(datetime(2026, 7, 18, 14, 30, tzinfo=IST),
                        datetime(2026, 7, 18, 17, 0, tzinfo=IST))
    partition = partition_of(corridor)

    # --- register participants ------------------------------------------------
    driver = Agent("did:web:drive.example:agent:d1", "driver-1", ["intercity_travel"],
                   {"intercity_travel": [Stance.SUPPLY]})
    engine.register_agent(driver)
    for name in ("a", "b", "c"):
        engine.register_agent(Agent(f"did:web:ride.example:agent:{name}", f"rider-{name}",
                                    ["intercity_travel"], {"intercity_travel": [Stance.DEMAND]}))
        # Riders keep the safe default (require_confirmation) — so the staged
        # proposal below will genuinely wait on an explicit approval call.
        engine.register_mandate(Mandate(f"m-{name}", f"rider-{name}", f"did:web:ride.example:agent:{name}",
                                        "intercity_travel", rupees(1000),
                                        autonomy_level=AutonomyLevel.REQUIRE_CONFIRMATION))

    # --- driver posts a ride that needs 3 seats to run ------------------------
    offer = Offer(
        offer_id="offer-1", issuer_ref=driver.agent_id, category_ref="intercity_travel",
        grouping_keys=corridor,
        capacity=Capacity(unit="seat", quantity=3, min_fill=3),  # won't run for < 3
        price=rupees(550), hold_expires_at=datetime(2026, 7, 17, 20, 0, tzinfo=IST),
        created_at=now,
        category_ext={"departure": departure, "route": [
            {"stop": "Pune", "eta": departure},
            {"stop": "Satara", "eta": departure + timedelta(hours=1, minutes=30),
             "price_per_seat": rupees(380)},
            {"stop": "Vadgaon", "eta": departure + timedelta(hours=2, minutes=15),
             "price_per_seat": rupees(430)},
            {"stop": "Ichalkaranji", "eta": departure + timedelta(hours=3, minutes=30),
             "price_per_seat": rupees(520)},
            {"stop": "Kolhapur", "eta": departure + timedelta(hours=4)},
        ]},
    )
    engine.submit_offer(offer)  # P11: fraud-filtered before entering the supply queue

    # --- three riders, three different waypoints, none matchable alone --------
    # solo_wait_seconds=0: escalate to the collaboration queue on the very
    # first failed solo attempt (P12) rather than waiting a real clock tick,
    # to keep this demo deterministic.
    for k, (name, drop) in enumerate((("a", "Satara"), ("b", "Vadgaon"), ("c", "Ichalkaranji"))):
        engine.submit_intent(Intent(
            intent_id=f"intent-{name}", issuer_ref=f"did:web:ride.example:agent:{name}",
            category_ref="intercity_travel", grouping_keys=corridor,
            constraints=Constraints(time_window=window, budget_ceiling=rupees(600), quantity=1),
            mandate_ref=f"m-{name}", created_at=now + timedelta(seconds=k),
            expiry=datetime(2026, 7, 18, 14, 0, tzinfo=IST),
            preferences={"drop_stop": drop}, coalition_opt_in=True, solo_wait_seconds=0,
        ))
    clock.advance(seconds=3)  # let every intent's (zero-second) wait timer clear

    # --- run the partition: staged proposal(s), not yet Commitments -----------
    proposals = engine.run_partition("intercity_travel", partition)
    print(f"proposals staged: {len(proposals)}")
    proposal = proposals[0]
    print(f"  {proposal.proposal_id[:8]}  kind={proposal.demand_kind}  "
          f"riders={len(proposal.demand_agents)}  total=Rs.{proposal.total_price.amount_minor // 100}  "
          f"status={proposal.status.value}  "
          f"provider_approved={proposal.provider_approved}  consumer_approved={proposal.consumer_approved}")
    assert proposal.status == ProposalStatus.PROPOSED, "should be waiting on rider approval"
    assert proposal.provider_approved is True, "posting the offer was the driver's blanket approval"
    assert proposal.consumer_approved is None, "riders require explicit confirmation"
    print(f"  notifications sent: {[e[1] for e in notifier.events]}")

    # --- the coalition's unanimous consent (docs/technical-deep-dive/02 §4)
    # is confirmed to the platform as a single consumer-side approval, and
    # funds are captured for all three riders' shares at once -------------
    commitment = engine.approve_proposal(proposal, side="consumer", approved=True)
    assert commitment is not None
    print(f"\ncommitment formed: {commitment.commitment_id[:8]}  "
          f"status={commitment.status.value}  escrow={commitment.escrow.state.value}  "
          f"(this is an AGREEMENT, not the final step)")

    # --- fulfillment window opens; no dispute; dual approval + evidence -------
    evidence = {"pickup_confirmed_at": departure, "dropoffs": [
        {"intent_ref": "intent-a", "stop": "Satara", "confirmed_at": departure + timedelta(hours=1, minutes=30)},
        {"intent_ref": "intent-b", "stop": "Vadgaon", "confirmed_at": departure + timedelta(hours=2, minutes=15)},
        {"intent_ref": "intent-c", "stop": "Ichalkaranji", "confirmed_at": departure + timedelta(hours=3, minutes=30)},
    ]}
    fulfillment, settlement = engine.fulfill(
        commitment, consumer_approved=True, provider_approved=True, evidence=evidence)
    print(f"\nfulfillment outcome: {fulfillment.outcome.value}")
    assert settlement is not None
    print(f"settlement: gross=Rs.{settlement.gross.amount_minor // 100}  "
          f"fee=Rs.{settlement.protocol_fee.amount_minor / 100:.2f}  "
          f"net_to_provider=Rs.{settlement.net_to_provider.amount_minor / 100:.2f}")

    # --- negative check: a mid-window dispute freezes escrow, blocks fulfill --
    print("\nmid-window dispute example (P13): a second, single-rider commitment")
    solo_commitment = _second_commitment(engine, corridor, window, now)
    dispute = engine.raise_dispute(solo_commitment, raised_by="consumer", reason_code="timing")
    print(f"  dispute raised: status={dispute.status.value}  escrow={solo_commitment.escrow.state.value}")
    try:
        engine.fulfill(solo_commitment, consumer_approved=True, provider_approved=True, evidence={})
        raise AssertionError("fulfill should have refused: a dispute is open")
    except Exception as e:
        print(f"  fulfill() correctly refused while disputed: {type(e).__name__}")
    resolved = engine.resolve_dispute(dispute, solo_commitment)
    print(f"  resolver decision: outcome={resolved.outcome.value}  "
          f"escrow remains={solo_commitment.escrow.state.value} (still frozen: escalated, not paid out)")


def _second_commitment(engine, corridor, window, now):
    """A minimal second offer + solo transaction, staged and approved, purely
    to demonstrate the dispute path without competing for offer-1's capacity
    (which the coalition above already fully consumed)."""
    from a2a_marketplace.models import AutonomyLevel, Offer as OfferModel

    engine.submit_offer(OfferModel(
        offer_id="offer-2", issuer_ref="did:web:drive.example:agent:d2",
        category_ref="intercity_travel", grouping_keys=corridor,
        capacity=Capacity(unit="seat", quantity=1, min_fill=1),
        price=rupees(550), hold_expires_at=datetime(2026, 7, 17, 20, 0, tzinfo=IST),
        created_at=now,
        category_ext={"departure": window.earliest, "route": [
            {"stop": "Pune", "eta": window.earliest},
            {"stop": "Kolhapur", "eta": window.earliest + timedelta(hours=4)},
        ]},
    ))
    engine.register_mandate(Mandate("m-d", "rider-d", "did:web:ride.example:agent:d",
                                    "intercity_travel", Money(100000, "INR"),
                                    autonomy_level=AutonomyLevel.AUTO_COMMIT_WITHIN_SCOPE))
    engine.submit_intent(Intent(
        intent_id="intent-d", issuer_ref="did:web:ride.example:agent:d",
        category_ref="intercity_travel", grouping_keys=corridor,
        constraints=Constraints(time_window=window, budget_ceiling=Money(100000, "INR"), quantity=1),
        mandate_ref="m-d", created_at=now, expiry=window.latest,
        preferences={"drop_stop": "Kolhapur"}, coalition_opt_in=False,
    ))
    proposals = engine.run_partition("intercity_travel", partition_of(corridor))
    proposal = next(p for p in proposals if "intent-d" in [d["intent_ref"] for d in p.detail["drops"]])
    # Both sides here use auto-commit mandates/offers, so the proposal is
    # already fully approved and finalized inside run_partition — no
    # separate approve_proposal() call needed (unlike the coalition above,
    # where riders required explicit confirmation).
    assert proposal.status == ProposalStatus.APPROVED
    return next(c for c in engine.storage.commitments.values() if c.demand_ref == "intent-d")


if __name__ == "__main__":
    main()
