# Freight & logistics — trucking capacity and backhaul matching

## 1. Why this fits the pattern

Purely B2B, much higher value per transaction than any other vertical
here, and the central pain point — **a truck that delivered a full load
one-way often drives back empty** — is *literally* the demand-aggregation
problem from the main design doc's Pune-Kolhapur example, just with
pallets instead of passengers. It's also the one vertical in this folder
where centralized versions of this idea have already been tried at scale
(Uber Freight, Convoy), which makes it a useful test of whether
*decentralizing* the matching (no single company owning the graph) changes
the outcome for the better or just adds complexity.

## 2. Today's pain

- **Carrier side (truck owner/small fleet):** after dropping a load in a
  city, the truck either deadheads home empty (pure cost, no revenue) or
  the dispatcher spends time calling brokers/load boards to find *any*
  return load, often accepting a bad rate because an empty truck driving
  home is worse than a cheap load driving home.
- **Shipper side:** needs a truck for a specific lane/date, posts to a
  load board or calls a broker, and has no visibility into which trucks
  are about to be empty nearby versus already committed elsewhere — pure
  information asymmetry the broker currently monetizes.
- **Existing centralized attempts** (Uber Freight, Convoy) reduced some of
  this friction but re-created a version of the original problem: one
  company sitting in the middle of every match, taking a cut, and setting
  matching priority — carriers and shippers are still not talking to each
  other directly, just to a different single intermediary.

## 3. Actors / provider types

- **Shipper agent** — represents the company with freight to move (lane,
  weight/volume, equipment type needed, pickup/delivery windows, rate
  ceiling).
- **Carrier agent** — represents an owner-operator or small fleet
  (available equipment, current position, upcoming known commitments,
  rate floor). Large fleets may run one agent managing many trucks
  simultaneously — closer to the "small firm dispatch agent" pattern from
  the home-services doc than to a single individual.
- **Broker agent (optional)** — some shippers/carriers will still want a
  broker's relationship and risk-absorption (broker guarantees payment,
  handles claims); the protocol should let a broker participate *as just
  another agent* with its own negotiation stance, not as a required
  central chokepoint.
- **Registry/discovery** — needs a live position/availability feed from
  carrier agents (where is this truck now, when does it become free) to
  make backhaul matching possible at all; this is a stronger real-time
  discovery requirement than any other vertical here.

## 4. Market structure

Almost entirely negotiable (unlike food ordering's fixed-catalog default):
rate per lane is a live negotiation between shipper and carrier agents,
constrained by fuel cost, distance, equipment type, and how badly the
carrier needs to avoid an empty return leg. Time windows are firmer than
in travel (a shipper's dock has a real appointment slot), but rate is
softer.

## 5. Worked example — this is the backhaul/pooling case directly

A carrier just dropped a full load in Chicago and is based in Detroit.
Driving back empty costs money; no full load exists Chicago→Detroit today
matching that exact window.

1. Carrier agent posts availability: Chicago → Detroit (or nearby),
   available from 2pm today, up to 40,000 lbs, rate floor $650.
2. No single shipper wants exactly that full load — but three shippers
   each have partial loads on segments of a similar corridor (Chicago→Ann
   Arbor, Ann Arbor→Detroit, plus a Chicago→Toledo leg that's roughly on
   the way), each too small to justify a dedicated truck alone.
3. Mirroring the main doc's consumer coalition (§5), but this time it's
   the **shipper agents cooperating with each other** (not consumer-side
   passengers, but structurally identical): they discover each other via
   the registry for that corridor/window, check load compatibility
   (stackable, compatible freight — the freight equivalent of the
   comfort/compatibility check in §6 of the main doc, except here it's
   about physical/regulatory compatibility of goods, not personal
   comfort), and merge into one **joint load offer**: three partial loads,
   one route, one combined rate.
4. Carrier agent evaluates the joint offer against its $650 floor — the
   combined rate clears it, accepts, picks up all three partial loads on
   the way.
5. Fulfillment confirmations happen per-leg (each shipper's cargo
   delivered at its own stop) even though it was one negotiated
   commitment — the settlement layer needs to split payment three ways
   against one truck's single trip, proportional to what was agreed.

## 6. Coalition/pooling angle

Both directions exist here, more symmetrically than in any other vertical
in this folder:

- **Shipper-side coalition** (worked example above) — several partial
  loads merging to fill one truck.
- **Carrier-side coalition** — less common but real: two small carriers
  splitting one large load neither can fully cover alone (e.g., a load
  needs two trucks' worth of capacity, no single available truck is big
  enough).

## 7. Price discovery / anti-cartel considerations

This is the highest-stakes vertical for the main doc's §7 concern, because
freight rates are exactly the kind of market where real-world rate-fixing
investigations have happened between logistics companies — the incentive
and the historical precedent for collusion are both stronger here than in
travel. Applying the market-clearing approach: sealed reservation
rates/ceiling rates per lane+window feeding a clearing algorithm, a
published reference rate band per lane (many freight indices — e.g. rate
benchmarking services — already exist and could seed this rather than
building from zero), and active monitoring for correlated rate movements
among carriers on the same lane that don't track real capacity tightness.
Given the B2B stakes, this vertical is a strong candidate for *requiring*
the market-clearing layer from day one rather than deferring it to v1 the
way the main doc's build order does for the travel MVP — the collusion
incentive is too real to launch a pure bilateral-negotiation version first.

## 8. Trust, safety & compliance caveats

- **Regulatory/insurance verification is non-negotiable up front**, not a
  soft reputation signal: carrier operating authority, insurance
  certificates, safety ratings (equivalent regulatory bodies vary by
  country) must gate whether a carrier agent's offers are even shown,
  the same way licensing gated home-services providers.
- **Cargo compatibility checks are physical/regulatory, not preference.**
  Mixing incompatible freight (hazmat with food-grade goods, for example)
  in a shared-load coalition is a compliance failure, not a comfort
  mismatch — this check needs to be authoritative (declared cargo class,
  verified where required), not agent-negotiated judgment.
- **Multi-party payment splitting** (worked example, step 5) needs a
  robust settlement design — three shippers paying one carrier off one
  joint commitment is a harder accounting problem than the two-party AP2
  mandate case the main doc assumes by default.
- **Liability chain on damage/delay** across a multi-shipper coalition
  load needs clear per-leg attribution, since a delay caused by one
  shipper's late pickup shouldn't be billed against another shipper's
  leg.

## 9. Why this could be high impact

Backhaul/empty-mile waste is a large, well-documented, purely economic
inefficiency (not a convenience problem like most of the other verticals
here) — it's pure cost with no offsetting benefit to anyone, which means
the ROI case for fixing it doesn't depend on behavior change or new
demand, only on better matching. It's also the vertical with the clearest
existing (if imperfect) centralized precedent to benchmark against, so
"did decentralizing this actually help" is directly measurable against
what Uber Freight/Convoy-style platforms already achieved.
