# Price discovery: mechanism design

`../design.md` §7 asserts that price shouldn't be a pure free-for-all
bilateral outcome, because that's collusion-prone. This doc works out
*which* mechanism actually produces price discovery, borrowing directly
from auction theory and market microstructure rather than inventing
something novel — this is a well-studied problem in other fields and
should be treated as one.

## 1. Four canonical mechanisms, evaluated for this setting

### (a) Posted-price / take-it-or-leave (the Uber model)

One party computes "the" price centrally and everyone else just
accepts or declines a dispatch at that price.

- **Pros:** simple, instant, no negotiation latency.
- **Cons here:** requires one party with global visibility and the
  authority to set price for everyone — which doesn't exist in this
  model by design (`03-provider-isolation-and-discovery.md` — no single
  party sees the whole graph, and no single party is supposed to control
  it). This mechanism is *why* Uber doesn't need a decentralized protocol
  in the first place; adopting it here would just mean re-centralizing
  control in whichever registry operator computes the posted price —
  contradicts the premise.
- **Verdict:** ruled out as the sole mechanism. Usable only for
  fixed-schedule providers (bus/rail) where the price genuinely isn't
  being discovered at all, just quoted (`../design.md` §4).

### (b) Bilateral alternating-offers bargaining (Rubinstein-style)

Two agents take turns proposing/countering; classical bargaining theory
(Rubinstein's alternating-offers model) shows this converges to a split
determined by the two parties' relative patience/discount factors.

- **Pros:** simple peer protocol, no central authority required, matches
  the default flow already specified in `../design.md` §10.
- **Cons here:** the theoretical outcome depends on agents' "patience"
  parameters — and if many provider agents run similar software with
  similarly-tuned patience/strategy parameters (likely, since a handful of
  agent-framework vendors will dominate implementations), their bargaining
  behavior becomes correlated *without any explicit coordination at all*.
  That's the "algorithmic collusion" risk `../design.md` §7 already flags —
  bilateral bargaining alone doesn't prevent it, it just makes the
  collusion implicit instead of explicit, which is harder to detect, not
  safer.
- **Verdict:** fine as a *local* negotiation protocol, but needs an
  external backstop (the reference band in §3 below) — never trusted as
  the sole price-discovery mechanism at scale.

### (c) Sealed-bid double auction (e.g., McAfee's mechanism)

Buyers and sellers submit sealed reservation prices to a neutral clearing
party; a clearing algorithm (McAfee's dominant-strategy double auction is
the standard reference — truthful bidding is each participant's best
strategy, and the mechanism is approximately budget-balanced) computes a
clearing price and allocation.

- **Pros:** strategy-proof (no incentive to misreport), doesn't require
  providers to see each other's bids (fits the isolation requirement in
  `03-provider-isolation-and-discovery.md` directly), well-studied,
  resistant to the correlated-behavior problem in (b) because the clearing
  price comes from an algorithm over sealed submissions, not from
  pairwise agent behavior.
- **Cons here:** needs enough simultaneous participants in a
  (corridor, time-bucket) shard to produce a meaningful clearing round —
  liquidity-dependent. Doesn't fit a single urgent request (one person's
  emergency plumber call, `../industries/home-services.md` §5) where
  there's no batch to clear against.
- **Verdict:** the right mechanism for **thick, schedulable markets** —
  batch-clear every few minutes on high-volume corridors, the same way
  real stock exchanges run periodic batch auctions for less-liquid
  instruments (and continuous trading only for liquid ones) — this is a
  direct, deliberate borrow from market microstructure, not an analogy of
  convenience.

### (d) Combinatorial auction (needed once bundling/pooling is involved)

Once coalitions (`02-consumer-collaboration-protocol.md`) or bundled
provider offers (`../industries/event-services.md`,
`../industries/freight-logistics.md`) are in play, bids are over
*bundles*, not single items — "these three drop-points as one trip," "this
venue+caterer+photographer as one package."

- **The winner-determination problem for general combinatorial auctions is
  NP-hard** — exact solving doesn't scale as the number of possible
  bundles grows combinatorially. This is a known result, not a design
  choice; it has to be engineered around, not wished away.
- **Practical mitigation: restrict the bundle space.** Don't allow
  arbitrary bundles — restrict to structurally simple ones (a bundle is a
  contiguous sequence of waypoints along one advertised route, per
  `../design.md` §5's route-decomposition design; or a small, pre-defined
  set of vendor-category slots per event, per
  `../industries/event-services.md`). This is exactly why the base
  protocol's waypoint-list offer schema matters technically, not just
  descriptively — it bounds the search space to something a
  branch-and-bound or greedy/LP-relaxation heuristic (the same class of
  approximate solver used in ad-exchange bundle auctions and airline
  crew-scheduling) can actually clear in real time, instead of facing the
  unrestricted NP-hard case.
- **Verdict:** required wherever pooling/bundling exists, but only
  tractable if the base protocol keeps bundle structure restricted by
  design — an open-ended "any subset of any offers" combinatorial auction
  is not buildable at real-time latency.

## 2. Recommended hybrid, staged by market thickness

| Market condition | Mechanism |
|---|---|
| Thin/urgent (single emergency home-services call, low-density rural corridor) | Bilateral bargaining (b), bounded rounds, checked against the reference band (§3) as a sanity backstop |
| Thick/scheduled (popular intercity corridor at commute hours, dense urban food-delivery zone) | Periodic batched sealed-bid double auction (c) |
| Bundled/pooled (coalitions, freight backhaul, event vendor bundles) | Constrained combinatorial auction (d), bundle space restricted to physically/structurally valid combinations |

None of these three is "the" mechanism — which one applies is a property
of the specific shard's liquidity and whether bundling is involved, and a
provider/consumer agent should expect to encounter all three depending on
context, the same way a trader encounters both continuous and batch
auction mechanisms on a single exchange depending on the instrument.

## 3. The reference price band (the backstop for (b), the anchor for all three)

Regardless of which mechanism clears a given negotiation, a published
**reference band** — e.g., trailing 14-day P25-P75 cleared price for that
(corridor, time-bucket, provider-type) — should be visible to all agents
before commitment (`../design.md` §7). This does two jobs:

- Gives bilateral bargaining (b) an external check so correlated-patience
  drift doesn't silently become the de facto price.
- Gives every agent — and the collusion-monitoring function — a baseline
  to detect when a cleared price (from any mechanism) has drifted
  suspiciously far from recent history without a corresponding real
  demand/supply shift.

## 4. What this doesn't solve yet

- Bootstrapping the reference band before enough historical data exists
  (cold-start problem, `06-caveats-and-practical-realities.md`).
- Exactly which heuristic solver to use for (d) at what bundle-size limit
  is an implementation question this doc deliberately leaves open — it's
  an engineering choice to make against a real workload, not a design
  decision to lock in speculatively.
- Cross-shard clearing (a bundle whose components span two different
  (corridor, time-bucket) shards) needs the overlapping-membership
  handling described in `01-scale-and-matching-architecture.md` §5, and
  hasn't been fully worked out for the combinatorial-auction case
  specifically.
