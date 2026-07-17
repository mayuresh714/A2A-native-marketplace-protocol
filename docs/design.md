# A2A-Native Marketplace Protocol — Design Doc (v0.2 draft)

## 1. Problem

Two-sided marketplaces for perishable, time-boxed capacity — intercity rides,
shared vans, private buses, seats on a scheduled route — currently force a
human on each side to do the matching:

- **Consumers** scroll lists of rides/drivers, guess who will actually accept,
  wait for a response, get rejected, repeat.
- **Providers** (drivers, small operators) have to keep an app open, watch
  fill rates, and manually reprice or reschedule when a ride isn't filling.

The inefficiency isn't the data (both sides' preferences are usually simple
and structured — time window, price, seats, route, detour tolerance) — it's
that a human has to sit in the loop doing search and back-and-forth that a
piece of software could do faster and continuously.

**Goal:** replace the human-in-the-loop search-and-haggle cycle with two
agents — one representing the consumer, one representing the provider — that
discover each other, negotiate terms, and commit, with humans only asked to
set preferences up front and approve/decline at defined checkpoints.

v0.1 of this doc scoped a single consumer agent negotiating with a single
provider agent, mutually known in advance. v0.2 (this revision) extends the
picture to what the market actually looks like: **many consumer agents and
many, mutually-unknown provider agents of different kinds, competing and
sometimes cooperating on the same route/time window** — and the market design
problem that comes with that (price discovery without letting competing
agents form a cartel).

Reference scenario used throughout this doc: intercity travel (>100km),
BlaBlaCar-style ride-sharing, private/chartered buses, and scheduled coach/rail
services — not local/on-demand cabs (Uber/Ola city rides), which are a
different matching problem (real-time, hyper-local, already well solved).

## 2. Prior art (checked before designing, July 2026)

| Project | What it actually is | Why it isn't this |
|---|---|---|
| **Google A2A (Agent2Agent)** — Linux Foundation, 150+ member orgs | Open protocol for agent discovery ("agent cards"), capability advertisement, and task lifecycle (send task, get status, stream results) between agents | It's transport/plumbing, not a marketplace semantic. It doesn't define "offer," "negotiate," "commit," or "escrow." Intended to be built on, not competed with. |
| **Google AP2 (Agent Payments Protocol)** | Extends A2A with "Intent Mandates" and "Cart Mandates" — cryptographically signed, human-authorized spend boundaries an agent can act within without asking every time | Solves the payment-authorization half of the problem, not the negotiation half. Worth reusing directly rather than reinventing. |
| **OpenAI + Stripe Agentic Commerce Protocol (ACP)**, and the competing **UCP** | Agent-to-merchant checkout: one shopping agent buys from one seller's catalog | One-directional (buyer agent → fixed catalog). No peer negotiation between two autonomous agents representing two different parties with competing objectives. |
| **Uber × OpenAI (ChatGPT app, 2026)** + "Uber Assistant" | A conversational front-end that calls Uber's own booking API; a driver-facing assistant for earnings advice | Single-vendor UX automation. No competing provider agents, no open wire protocol, no negotiation — it's a chat skin on one company's existing backend. |
| **Uber's own dispatch/surge pricing** | Uber solves multi-driver competition by *removing* price negotiation entirely: Uber's central algorithm sets the price, drivers only accept/decline a dispatch | Relevant as a cautionary contrast (see §7): it works because one company controls the whole graph. This protocol has no such single controller by design, so it needs a different answer to "who sets the price." |
| **BlaBlaCar ML matching** | Ranks/filters/hides rides using ML ("Boost rides") | Improves the human's search results; the human still swipes/accepts/rejects manually. No agent commits on the human's behalf, and no cross-passenger pooling beyond what the driver manually offers. |

**The gap:** no open protocol exists for many independent, self-interested
software agents — representing different companies or individuals, of
different provider types, with no shared backend — to discover each other,
negotiate, pool, and commit, while keeping price discovery fair rather than
collusive. That's the space this project is in.

## 3. Strong points of the idea

- **Collapses search cost.** Consumer states intent once; the agent handles
  discovery, comparison, and re-negotiation continuously, including at 2am
  when no human is watching.
- **Unlocks matches humans wouldn't find.** A provider agent can propose a
  time/price/detour a human would never have bothered to type out, and a
  consumer agent can evaluate 50 such counter-offers instantly.
- **Provider-side automation is symmetric and valuable on its own.** A
  driver's agent can auto-adjust price or timing when a route is under-filled
  instead of the driver manually checking an app.
- **Standardization beats N closed apps.** If consumer and provider agents
  speak a common protocol, a consumer isn't locked into whichever single
  app a provider chose to list on.
- **Naturally decentralizable.** Nothing about negotiation requires a single
  central matching server; it can be a registry + direct agent-to-agent
  channel, lowering the platform's own operating leverage/lock-in over both
  sides — a deliberate contrast to how BlaBlaCar/Uber monetize via being the
  sole intermediary.

## 4. Market structure: many providers, many kinds of providers

The realistic version of this market is **n-to-m and heterogeneous**, not
one consumer agent talking to one pre-chosen provider agent:

- Many consumers want the same corridor around the same time (say, ~30
  people wanting Pune → Kolhapur on a given afternoon).
- Many, mutually unknown providers compete for that demand, and they are
  **not all the same kind of thing**:
  - individual drivers/car owners offering a shared ride,
  - small ride-pooling operators running a van/shared-taxi service,
  - private tour/charter bus operators,
  - scheduled state/private bus corporation routes (fixed schedule, fixed
    price, fixed stops),
  - railway (fixed schedule, fixed price, high capacity, but bookable well
    in advance and inflexible on timing).

  These compete on price and time-fit, but also on very different axes
  (comfort, fixed vs flexible schedule, luggage, reliability) — a provider
  agent's "offer" schema needs to represent enough of that for a consumer
  agent to compare a ₹550 shared-car seat against a ₹300 fixed-time bus
  seat against a ₹450 train seat honestly. Fixed-schedule providers (bus
  corporations, rail) don't negotiate price or time at all — their agent's
  role is closer to "quote + book" than "negotiate," and the protocol has to
  accommodate a provider agent that never counter-offers.
- Providers don't know about each other by default, and shouldn't need to —
  discovery is opt-in via a registry query for a route/time (reusing A2A's
  discovery pattern), not a hardcoded list of competitors.

**Why this isn't "just let each provider agent set its own price freely":**
Uber's answer to multi-driver competition is to remove price-setting from
drivers entirely — one company's algorithm decides the fare, drivers only
accept or decline. That works, but only because one company controls 100%
of the graph and is accountable for the pricing algorithm. This protocol
has no single controlling company by design — providers are independent
individuals and companies who don't answer to a common employer. Naive
free-for-all bilateral pricing among *mutually competing but structurally
similar* agents is exactly the setup where tacit or explicit price-fixing
becomes possible (see §7) — that has to be designed against from the start,
not patched in later.

## 5. Demand aggregation & consumer-agent collaboration

This is the mechanism that makes the protocol worth more than a faster
version of today's apps: **consumer agents cooperating with each other**,
not just with provider agents, to turn several unviable individual matches
into one viable pooled one.

### Worked example

A driver's provider agent posts capacity: Pune → Kolhapur, 15:30–16:30
departure, 3 seats. No consumer agent wants exactly Kolhapur at exactly
that window, so on a naive single-origin/single-destination matcher, this
ride gets zero matches and the driver eventually cancels or reprices —
today's actual pain point.

Meanwhile three separate consumer agents are each independently stuck:
one wants Pune → Satara, one Pune → Vadgaon, one Pune → Ichalkaranji — all
waypoints along the same Pune–Kolhapur corridor — each with a flexible-ish
time window that doesn't line up with a decent train/bus slot, and none of
whom individually justifies a driver taking that specific detour-laden trip
for one fare.

Bilateral matching (one consumer agent ↔ one provider agent) fails all four
parties. The fix has two layers:

1. **Route decomposition.** A provider agent shouldn't advertise a single
   origin-destination pair — it advertises a route as an **ordered list of
   waypoints**, each with its own capacity and per-segment price, so "I'm
   driving Pune → Kolhapur via Satara/Karad/Ichalkaranji" is a first-class,
   queryable offer, not an opaque single O-D string. This alone lets each
   of the three consumer agents find the *provider* agent. It does not by
   itself make the trip worth the driver's time, and it doesn't resolve
   three different desired departure times into one.

2. **Consumer coalition formation.** When a consumer agent can't get a good
   solo match, it opts in (only if its human has allowed this — see §6) to
   a short-lived coalition-discovery pool for that corridor/time window.
   Consumer agents in that pool talk **directly to each other**, not just to
   the provider: they compare time windows, check compatibility (§6), and if
   they can converge on a departure time all three can live with, they merge
   into a **single joint counter-offer** — "3 seats, drop at
   Satara/Vadgaon/Ichalkaranji in that order, combined fare X, depart 15:45"
   — which is a much better proposal for the driver's agent to accept than
   three separate uncertain bilateral offers, and usually a lower per-seat
   price for each rider than any of them would get solo.

This is the concrete version of "agents unlock value humans wouldn't
bother finding": no human individually had the patience to notice that
three unrelated people's mediocre options combine into one good ride.

A coalition is **ephemeral** — formed for one negotiation, dissolved the
moment it books or fails, never a standing group. There's no requirement
that coalition members ever interact again or know who the others are
beyond what's needed to complete this one trip.

## 6. Compatibility & comfort preferences

Coalition formation means an agent may propose putting its human in a
vehicle with strangers chosen algorithmically. People have legitimate,
personal comfort constraints about that — the driving examples from real
usage: a woman preferring not to share with unfamiliar men, a young couple
preferring not to share with a much older or unrelated group, and similar.
These have to be first-class, not an afterthought:

- **Trip-scoped and opt-in.** A comfort preference is set per trip (or as a
  reusable default the human explicitly turns on), never inferred by the
  agent and never a permanent stored profile of a protected characteristic.
  The human can change or clear it at any time.
- **Symmetric evaluation.** Before proposing a coalition, agents check both
  sides' constraints against each other, and a coalition is only proposed
  when it clears for everyone in it.
- **Rejection reasons stay private to the rejecting agent's principal.**
  If a coalition doesn't clear because of a comfort mismatch, the other
  party's agent should see "no compatible group found," never the specific
  reason. Surfacing "you were excluded because of your gender/age/group"
  as an explicit system message is both bad experience and a real
  discrimination/legal-exposure risk — the routing-around has to be silent.
- **Human confirmation before finalizing any stranger coalition.** Even
  with a pre-authorized budget/time mandate (§8's Intent Mandate), booking
  a shared ride with people your agent picked algorithmically is a
  different risk class from booking a solo commercial trip, and should
  require an explicit human confirm step by default, not silent
  auto-commit — this can be relaxed later per-user, but shouldn't be the
  default.
- **Legal/regulatory review flag.** Anti-discrimination law differs by
  jurisdiction and differs between "a commercial service refusing a
  customer" and "a private individual choosing who they personally
  travel with." This doc records the product requirement; it is
  explicitly *not* a legal clearance, and needs jurisdiction-specific
  review before this ships anywhere.

## 7. Price discovery & anti-cartel safeguards

This is the part of the design that most needs to get right, and the part
most likely to be gotten wrong by default: **if every provider agent is
free to set whatever price it wants in every bilateral negotiation, nothing
stops a set of nominally competing agents from converging on inflated
prices** — either through explicit coordination (a literal cartel) or
through *algorithmic* collusion, where independently-run pricing agents
that see the same concentrated-demand signal (a rainy Friday, a festival
weekend, a corridor with no other options) each learn on their own to push
price up at exactly the moment consumers have the least alternative. This
is a documented real antitrust concern in other algorithmic-pricing
markets, and it is more likely here, not less, precisely because the
protocol makes many independent agents' pricing responsive to the same
shared, visible demand signals in real time.

Design response — price is not purely a bilateral negotiation outcome:

- **A neutral market-clearing layer**, operated by the registry/consortium
  (not by any provider, and not by one dominant company either), computes a
  reference/clearing price band per route+time-bucket from aggregate
  submitted supply and demand:
  - provider agents submit capacity + a reservation (floor) price for a
    route/time-bucket, sealed from other providers;
  - consumer agents (and coalitions) submit demand + a ceiling price,
    sealed similarly;
  - a clearing algorithm computes an allocation and a reference price band
    for that bucket. Because pooled, multi-waypoint trips (§5) are
    literally bundles, this is a combinatorial-auction problem, not a
    simple single-item auction — closer in kind to wholesale
    electricity-market clearing than to a simple price-matching engine.
- **The reference band is visible to all agents before commitment.**
  A provider agent can still offer above or below it, but a consumer
  agent can see when an offer is priced far outside the band for that
  route/time and treat that as a signal, the same way a regulator capping
  Uber's surge multiplier gives riders a ceiling to check against.
- **Collusion monitoring is a governance function, not just a technical
  one.** Track price movements across nominally independent, competing
  provider agents on the same corridor; correlated moves that don't track
  a real supply/demand shift get flagged, and those agents' offers get
  quarantined pending review — analogous to exchange-side market
  surveillance, not something an individual consumer agent can detect on
  its own.
- **This is deliberately not Uber's model.** Uber's fairness (such as it
  is) rests on one company being accountable for one pricing algorithm.
  Here price is meant to emerge from an open, auditable mechanism fed by
  many independent providers — which is the actual point of doing this as
  an open protocol rather than another single closed platform — but that
  only holds if the clearing/anti-collusion layer is real and independently
  operated, not hand-waved.

This is the least mature section of the design and likely needs outside
market-design/mechanism-design expertise, not just software engineering —
flagged explicitly rather than assumed solved.

## 8. Actors

- **Consumer Agent** — acts for the traveler. Holds preferences (route, time
  window, budget, seat count, detour tolerance, comfort constraints) and an
  Intent Mandate from the human.
- **Provider Agent** — acts for a driver, small operator, or bus/coach/rail
  service. Subtypes, since they don't all behave the same way:
  - *Individual driver* — negotiates price/time/route freely.
  - *Pooling/van operator* — similar, usually multi-seat.
  - *Private tour/charter operator* — negotiates in bulk/whole-vehicle terms.
  - *Scheduled public transport (bus corp)* — fixed schedule and price;
    agent role is quote-and-book, not negotiate.
  - *Railway* — fixed schedule/price, booked in advance, highest capacity,
    least flexible; same quote-and-book role.
- **Consumer Coalition** — an ephemeral, opt-in grouping of consumer agents
  formed to make one joint offer (§5); not a standing entity.
- **Registry / Discovery layer** — lets agents find each other and find
  coalition-discovery pools for a given route/time, without a single
  central matchmaker brokering every deal (reuses A2A's agent-card
  discovery pattern).
- **Market Clearing / Price Reference service** (§7) — computes and
  publishes reference price bands per route+time-bucket, and runs
  collusion monitoring. Must be operated neutrally (open-source reference
  implementation and/or a multi-party consortium), never by a single
  provider or by whoever happens to run the biggest registry.
- **Trust/Attestation service (optional, pluggable)** — issues or verifies
  identity and reputation attestations (driver verified, past-trip ratings)
  that agents can request from each other during negotiation.

## 9. Protocol layering

```
┌─────────────────────────────────────────────┐
│  Marketplace Negotiation Layer  (this repo)  │  Intent → Offer → Coalition →
│                                               │  Commit → Fulfillment → Settle
├───────────────────────┬───────────────────────┤
│  AP2 (Agent Payments)  │  Market Clearing /     │  payment mandates |
│                        │  Price Reference (§7)  │  price bands, anti-collusion
├───────────────────────┴───────────────────────┤
│  A2A (Agent2Agent Protocol)                  │  agent discovery, capability
│                                               │  cards, task lifecycle, transport
└─────────────────────────────────────────────┘
```

This project defines the top layer plus the market-clearing service
alongside AP2 — both sit on A2A for transport/discovery, and neither
reimplements it.

## 10. Core message flow

```
Consumer Agents (1..n)                 Provider Agent(s) (1..m)
      │                                        │
      │ 1. TripIntent (route/time/budget)      │
      │ ──────────────────────────────────────>│
      │                                        │
      │ 2a. Solo Offer                         │
      │ <──────────────────────────────────────│   (bilateral path, §1.1 flow)
      │                                        │
      │ 2b. If no good solo match: opt into    │
      │     coalition-discovery pool           │
      │ <────────────────────────────────────>  │   (peer, consumer-to-consumer)
      │  compatibility check (§6) + time        │
      │  convergence between consumer agents    │
      │                                         │
      │ 3. Joint CoalitionOffer                │
      │ ──────────────────────────────────────>│
      │                                        │
      │ 4. Accept / Counter (bounded rounds)   │
      │ <──────────────────────────────────────│
      │                                        │
      │ 5. Commitment (hold, expiry, mandate,  │
      │    price checked against §7 band)      │
      │ <──────────────────────────────────────│
      │                                        │
      │ 6. Payment authorization (AP2)         │
      │ ──────────────────────────────────────>│
      │                                        │
      │ 7. Fulfillment confirmation            │
      │ <──────────────────────────────────────│
      │                                        │
      │ 8. Reputation/feedback record          │
      │ <──────────────────────────────────────│
```

Negotiation rounds are bounded (max N or a timeout) to avoid unbounded
back-and-forth; either agent — or any human behind a coalition member —
can escalate or withdraw at any point.

## 11. Draft message schemas (illustrative, not final)

```json
// TripIntent — consumer agent → registry/provider agents
{
  "type": "trip_intent",
  "intent_id": "uuid",
  "origin": {"city": "Pune", "lat": 18.52, "lng": 73.85},
  "destination": {"city": "Satara", "lat": 17.69, "lng": 74.00},
  "earliest_departure": "2026-07-18T14:30:00+05:30",
  "latest_departure": "2026-07-18T17:00:00+05:30",
  "seats": 1,
  "max_price_per_seat": {"amount": 400, "currency": "INR"},
  "coalition_opt_in": true,
  "comfort_prefs": ["female_co_passengers_only"],
  "mandate_ref": "ap2-intent-mandate-uuid"
}

// Offer — provider agent advertises a route as waypoints, not one O-D pair
{
  "type": "offer",
  "offer_id": "uuid",
  "provider_agent_id": "did:example:provider-123",
  "provider_type": "individual_driver",
  "route": [
    {"stop": "Pune",          "depart": "2026-07-18T15:30:00+05:30"},
    {"stop": "Satara",        "eta": "2026-07-18T17:00:00+05:30", "price_per_seat": {"amount": 380, "currency": "INR"}},
    {"stop": "Vadgaon",       "eta": "2026-07-18T17:45:00+05:30", "price_per_seat": {"amount": 430, "currency": "INR"}},
    {"stop": "Ichalkaranji",  "eta": "2026-07-18T19:00:00+05:30", "price_per_seat": {"amount": 520, "currency": "INR"}},
    {"stop": "Kolhapur",      "eta": "2026-07-18T19:30:00+05:30", "price_per_seat": {"amount": 550, "currency": "INR"}}
  ],
  "seats_available": 3,
  "hold_expires_at": "2026-07-17T15:40:00+05:30",
  "reputation_ref": "attestation-uuid"
}

// CoalitionProposal — consumer agent → consumer agent (peer, not via provider)
{
  "type": "coalition_proposal",
  "coalition_id": "uuid",
  "corridor": "Pune-Kolhapur",
  "proposer_intent_id": "uuid",
  "candidate_intent_ids": ["uuid-2", "uuid-3"],
  "proposed_departure": "2026-07-18T15:45:00+05:30",
  "compatibility_result": "cleared"
}

// CoalitionOffer — coalition → provider agent, joint counter-offer
{
  "type": "coalition_offer",
  "coalition_id": "uuid",
  "offer_id": "uuid",
  "members": [
    {"intent_id": "uuid-1", "drop_stop": "Satara"},
    {"intent_id": "uuid-2", "drop_stop": "Vadgaon"},
    {"intent_id": "uuid-3", "drop_stop": "Ichalkaranji"}
  ],
  "proposed_departure": "2026-07-18T15:45:00+05:30",
  "total_price": {"amount": 1250, "currency": "INR"}
}

// MarketPriceSignal — clearing service → agents (§7)
{
  "type": "market_price_signal",
  "corridor": "Pune-Kolhapur",
  "time_bucket": "2026-07-18T15:00/17:00+05:30",
  "reference_band": {"low": 480, "high": 560, "currency": "INR"},
  "basis": "cleared_auction | historical_percentile"
}

// Commitment
{
  "type": "commitment",
  "offer_id": "uuid",
  "status": "held | confirmed",
  "hold_expires_at": "2026-07-17T15:45:00+05:30",
  "price_within_reference_band": true,
  "cart_mandate_ref": "ap2-cart-mandate-uuid"
}
```

## 12. Caveats / open problems

- **Authorization boundaries.** An agent must never commit a human to spend
  or travel beyond what was explicitly authorized. Adopt AP2's mandate
  model (Intent Mandate + Cart Mandate); coalition bookings additionally
  need an explicit human confirm step by default (§6).
- **Algorithmic collusion / cartel risk (§7).** The single biggest
  systemic risk in this design — independent provider agents converging on
  inflated pricing, explicitly or tacitly. Requires a neutral market
  clearing/reference-price layer and active collusion monitoring; not
  solvable by protocol messages alone, needs governance.
- **Compatibility-preference legal exposure (§6).** Comfort-based
  co-passenger matching is a real user need but sits close to
  anti-discrimination law; needs jurisdiction-specific legal review before
  any real deployment, and rejection reasons must never be disclosed to
  the rejected party.
- **Coalition trust.** A stranger's agent could misrepresent its own
  compatibility answers or timing flexibility to force a match; coalition
  commitments still need a human confirm checkpoint and should carry
  reputation consequences for agents that renege after a coalition forms.
- **Trust, identity, fraud generally.** Sybil provider agents, fake
  vehicle/capacity claims, agent impersonation. Needs a signed
  identity/reputation primitive in the protocol, not a platform-side
  afterthought.
- **Liability and regulation.** Intercity transport is licensed; "my agent
  committed me" needs an auditable, non-repudiable record of exactly what
  was authorized and agreed.
- **Perishable inventory / race conditions.** A seat can vanish mid
  negotiation or mid coalition-formation. Needs explicit hold-with-expiry
  semantics so two consumer agents (or coalitions) can't both believe they
  hold the same seat.
- **Latency vs. real-time expectations.** Coalition formation adds an extra
  round of peer negotiation on top of provider negotiation; needs a
  timeout after which an agent falls back to its best solo offer rather
  than waiting indefinitely for a coalition to converge.
- **Cold-start liquidity.** All of the above (coalitions especially) need
  enough simultaneous agents in a corridor/time-bucket to be worth
  anything. Plan for a simulator/testbed phase before any real pilot.

## 13. Scope for v0 (what to actually build first)

Deliberately staged from simplest to hardest, because the hardest piece
(collusion-resistant market clearing) is not worth building before the
basic bilateral case is proven:

1. **v0 — spec + simulator, single provider type, bilateral only.** Define
   the negotiation message schema/state machine precisely; scripted
   consumer and provider agents negotiate synthetic trip intents. Validate
   multi-round negotiation, hold expiry/races, decline/timeout paths.
2. **v0.5 — multi-provider-type competition.** Add route decomposition
   (waypoint offers) and mixed provider types (individual/pooling/charter/
   fixed-schedule) competing for the same simulated demand.
3. **v0.7 — consumer coalitions.** Add peer-to-peer consumer negotiation,
   compatibility matching (§6), and joint coalition offers, still in
   simulation.
4. **v1 — market clearing / anti-cartel layer (§7).** The least proven
   part; likely needs a research/mechanism-design collaboration, not just
   an engineering sprint.
5. **Real pilot** on a single narrow corridor with consenting drivers only
   after the above are validated in simulation, with manual fallback for
   anything the protocol doesn't yet cover.

## 14. Explicitly out of scope for now

- Local/on-demand city rides (different problem, well-served already).
- Cross-border regulatory/licensing handling.
- A proprietary central matching engine — the point is agents negotiating
  and clearing directly through an open mechanism, not another closed
  platform in the middle.
