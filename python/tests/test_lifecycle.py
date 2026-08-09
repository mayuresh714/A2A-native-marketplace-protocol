"""End-to-end and principle-enforcement tests."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from a2a_marketplace import MarketplaceEngine, IntercityTravelCategory
from a2a_marketplace.adapters import (
    AllowAllIdentity,
    FixedClock,
    InMemoryStorage,
    PriceAscRanking,
    SimEscrow,
)
from a2a_marketplace.errors import MandateViolationError
from a2a_marketplace.models import (
    Agent,
    Capacity,
    Coalition,
    Constraints,
    EscrowState,
    Intent,
    Mandate,
    Money,
    Offer,
    Stance,
    TimeWindow,
    partition_of,
)

IST = timezone(timedelta(hours=5, minutes=30))


def rupees(n: int) -> Money:
    return Money(n * 100, "INR")


def make_engine(fee_bps: int = 200) -> MarketplaceEngine:
    cat = IntercityTravelCategory()
    return MarketplaceEngine(
        storage=InMemoryStorage(),
        clock=FixedClock(datetime(2026, 7, 17, 9, 0, tzinfo=IST)),
        ranking=PriceAscRanking(),
        escrow=SimEscrow(),
        identity=AllowAllIdentity(),
        categories={cat.id: cat},
        fee_bps=fee_bps,
    )


CORRIDOR = {"source_region": "Pune", "destination_region": "Kolhapur",
            "start_time_bucket": "2026-07-18T15:00/17:00+05:30"}
DEP = datetime(2026, 7, 18, 15, 30, tzinfo=IST)
WINDOW = TimeWindow(datetime(2026, 7, 18, 14, 30, tzinfo=IST),
                    datetime(2026, 7, 18, 17, 0, tzinfo=IST))


def _offer(min_fill: int, seats: int = 3) -> Offer:
    return Offer(
        offer_id="offer-1", issuer_ref="did:web:d:1", category_ref="intercity_travel",
        grouping_keys=CORRIDOR, capacity=Capacity("seat", seats, min_fill=min_fill),
        price=rupees(550), hold_expires_at=datetime(2026, 7, 17, 20, 0, tzinfo=IST),
        created_at=datetime(2026, 7, 17, 9, 0, tzinfo=IST),
        category_ext={"departure": DEP, "route": [
            {"stop": "Pune", "eta": DEP},
            {"stop": "Satara", "eta": DEP + timedelta(hours=1), "price_per_seat": rupees(380)},
            {"stop": "Vadgaon", "eta": DEP + timedelta(hours=2), "price_per_seat": rupees(430)},
            {"stop": "Ichalkaranji", "eta": DEP + timedelta(hours=3), "price_per_seat": rupees(520)},
        ]},
    )


def _intent(name: str, drop: str, budget: int = 600, i: int = 0) -> Intent:
    return Intent(
        intent_id=f"intent-{name}", issuer_ref=f"did:web:r:{name}",
        category_ref="intercity_travel", grouping_keys=CORRIDOR,
        constraints=Constraints(WINDOW, rupees(budget), 1),
        mandate_ref=f"m-{name}", created_at=datetime(2026, 7, 17, 9, i, tzinfo=IST),
        expiry=datetime(2026, 7, 18, 14, 0, tzinfo=IST),
        preferences={"drop_stop": drop}, coalition_opt_in=True,
    )


def _register_riders(engine, names, budget=1000):
    for n in names:
        engine.register_mandate(Mandate(f"m-{n}", f"r-{n}", f"did:web:r:{n}",
                                        "intercity_travel", rupees(budget)))


def test_solo_match_when_offer_needs_one():
    engine = make_engine()
    _register_riders(engine, ["a"])
    engine.submit_offer(_offer(min_fill=1))
    engine.submit_intent(_intent("a", "Satara"))
    commitments = engine.run_partition("intercity_travel", partition_of(CORRIDOR))
    assert len(commitments) == 1
    assert commitments[0].demand_kind == "intent"


def test_coalition_forms_only_on_solo_failure():
    engine = make_engine()
    _register_riders(engine, ["a", "b", "c"])
    engine.submit_offer(_offer(min_fill=3))  # won't run for a single rider
    for k, (n, drop) in enumerate([("a", "Satara"), ("b", "Vadgaon"), ("c", "Ichalkaranji")]):
        engine.submit_intent(_intent(n, drop, i=k))
    commitments = engine.run_partition("intercity_travel", partition_of(CORRIDOR))
    assert len(commitments) == 1
    c = commitments[0]
    assert c.demand_kind == "coalition"
    assert len(c.demand_agents) == 3
    # additive price: 380 + 430 + 520
    assert c.total_price == rupees(380 + 430 + 520)
    assert c.escrow.state == EscrowState.HELD


def test_settlement_requires_all_three_gates():
    engine = make_engine(fee_bps=200)
    _register_riders(engine, ["a", "b", "c"])
    engine.submit_offer(_offer(min_fill=3))
    for k, (n, drop) in enumerate([("a", "Satara"), ("b", "Vadgaon"), ("c", "Ichalkaranji")]):
        engine.submit_intent(_intent(n, drop, i=k))
    commitment = engine.run_partition("intercity_travel", partition_of(CORRIDOR))[0]

    evidence = {"dropoffs": [{"intent_ref": f"intent-{n}", "confirmed_at": DEP}
                            for n in ("a", "b", "c")]}

    # missing provider approval -> disputed, no money moves
    f1, s1 = engine.fulfill(commitment, consumer_approved=True,
                            provider_approved=False, evidence=evidence)
    assert s1 is None
    assert commitment.escrow.state == EscrowState.DISPUTED

    # all three gates -> settle with 2% fee
    commitment.escrow.state = EscrowState.HELD  # reset for the positive case
    f2, s2 = engine.fulfill(commitment, consumer_approved=True,
                            provider_approved=True, evidence=evidence)
    assert s2 is not None
    assert s2.gross == rupees(1330)
    assert s2.protocol_fee == Money(133000 * 200 // 10000, "INR")  # 2%
    assert s2.net_to_provider == s2.gross.minus(s2.protocol_fee)
    assert commitment.escrow.state == EscrowState.RELEASED


def test_no_evidence_blocks_settlement():
    engine = make_engine()
    _register_riders(engine, ["a", "b", "c"])
    engine.submit_offer(_offer(min_fill=3))
    for k, (n, drop) in enumerate([("a", "Satara"), ("b", "Vadgaon"), ("c", "Ichalkaranji")]):
        engine.submit_intent(_intent(n, drop, i=k))
    commitment = engine.run_partition("intercity_travel", partition_of(CORRIDOR))[0]
    _, settlement = engine.fulfill(commitment, consumer_approved=True,
                                   provider_approved=True, evidence={})
    assert settlement is None


def test_supply_coalition_is_forbidden_by_construction():
    """P1: provider-side coalitions must be impossible to construct."""
    with pytest.raises(ValueError):
        Coalition(coalition_id="x", member_intent_refs=["a", "b"],
                  proposed_departure=DEP, total_price=rupees(100), stance=Stance.SUPPLY)


def test_mandate_ceiling_is_enforced_in_code():
    """P4/P8: an over-budget commitment is blocked by the engine, not trusted."""
    engine = make_engine()
    # rider mandate ceiling below the Ichalkaranji fare
    engine.register_mandate(Mandate("m-a", "r-a", "did:web:r:a", "intercity_travel", rupees(400)))
    engine.submit_offer(_offer(min_fill=1))
    engine.submit_intent(_intent("a", "Ichalkaranji", budget=600))  # constraint passes (520<600)
    with pytest.raises(MandateViolationError):
        engine.run_partition("intercity_travel", partition_of(CORRIDOR))
