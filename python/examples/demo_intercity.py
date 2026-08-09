"""End-to-end demo: the Pune–Kolhapur coalition scenario from docs/design.md §5.

Run it::

    cd python && python examples/demo_intercity.py

It shows the whole lifecycle: a driver posts a ride that needs 3 seats to run;
three riders each wanting a different waypoint can't match solo, pool into one
coalition, commit into escrow, get fulfilled with dual approval + evidence, and
settle with a thin fee.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from a2a_marketplace import MarketplaceEngine, IntercityTravelCategory
from a2a_marketplace.adapters import (
    AllowAllIdentity,
    FixedClock,
    InMemoryStorage,
    PriceAscRanking,
    SimEscrow,
)
from a2a_marketplace.models import (
    Agent,
    Capacity,
    Constraints,
    Intent,
    Mandate,
    Money,
    Offer,
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
    engine = MarketplaceEngine(
        storage=InMemoryStorage(),
        clock=clock,
        ranking=PriceAscRanking(),
        escrow=SimEscrow(),
        identity=AllowAllIdentity(),
        categories={cat.id: cat},
        fee_bps=200,  # 2%
    )

    corridor = {"source_region": "Pune", "destination_region": "Kolhapur",
                "start_time_bucket": "2026-07-18T15:00/17:00+05:30"}
    departure = datetime(2026, 7, 18, 15, 30, tzinfo=IST)
    window = TimeWindow(datetime(2026, 7, 18, 14, 30, tzinfo=IST),
                        datetime(2026, 7, 18, 17, 0, tzinfo=IST))

    # --- register participants ------------------------------------------------
    driver = Agent("did:web:drive.example:agent:d1", "driver-1", ["intercity_travel"],
                   {"intercity_travel": [Stance.SUPPLY]})
    engine.register_agent(driver)
    for name in ("a", "b", "c"):
        engine.register_agent(Agent(f"did:web:ride.example:agent:{name}", f"rider-{name}",
                                    ["intercity_travel"], {"intercity_travel": [Stance.DEMAND]}))
        engine.register_mandate(Mandate(f"m-{name}", f"rider-{name}", f"did:web:ride.example:agent:{name}",
                                        "intercity_travel", rupees(1000)))

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
    engine.submit_offer(offer)

    # --- three riders, three different waypoints, none matchable alone --------
    for name, drop in (("a", "Satara"), ("b", "Vadgaon"), ("c", "Ichalkaranji")):
        engine.submit_intent(Intent(
            intent_id=f"intent-{name}", issuer_ref=f"did:web:ride.example:agent:{name}",
            category_ref="intercity_travel", grouping_keys=corridor,
            constraints=Constraints(time_window=window, budget_ceiling=rupees(600), quantity=1),
            mandate_ref=f"m-{name}", created_at=now + timedelta(minutes=ord(name)),
            expiry=datetime(2026, 7, 18, 14, 0, tzinfo=IST),
            preferences={"drop_stop": drop}, coalition_opt_in=True,
        ))

    # --- run the partition ----------------------------------------------------
    commitments = engine.run_partition("intercity_travel", partition_of(corridor))

    print(f"commitments formed: {len(commitments)}")
    for c in commitments:
        drops = [d["intent_ref"] for d in c.detail["drops"]]
        print(f"  {c.commitment_id[:8]}  kind={c.demand_kind}  "
              f"riders={len(c.demand_agents)}  total=Rs.{c.total_price.amount_minor // 100}  "
              f"escrow={c.escrow.state.value}  drops={drops}")

    assert len(commitments) == 1, "expected the three riders to pool into ONE ride"
    commitment = commitments[0]

    # --- fulfill: dual approval + evidence -> settlement ----------------------
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

    # --- a fraud check: money never moves without evidence --------------------
    print("\nnegative check: withholding evidence must block settlement")
    bad_commitment = _dummy_commitment(engine, offer, now)
    _, bad_settlement = engine.fulfill(
        bad_commitment, consumer_approved=True, provider_approved=True, evidence={})
    assert bad_settlement is None
    print("  -> no settlement produced, escrow stays disputed. Good.")


def _dummy_commitment(engine, offer, now):
    from a2a_marketplace.models import Commitment, Escrow
    c = Commitment(
        commitment_id="c-bad", offer_ref=offer.offer_id, demand_ref="intent-a",
        demand_kind="intent", supply_agent=offer.issuer_ref, demand_agents=["x"],
        total_price=Money(38000, "INR"), departure=now, escrow=Escrow(amount=Money(38000, "INR")),
        mandate_refs=["m-a"], created_at=now, detail={"drops": [{"intent_ref": "intent-a"}]})
    engine.escrow.hold(c)
    engine.storage.save_commitment(c)
    return c


if __name__ == "__main__":
    main()
