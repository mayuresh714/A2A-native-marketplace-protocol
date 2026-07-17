# A2A-Native Marketplace Protocol — Design Doc (v0.1 draft)

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

Reference scenario used throughout this doc: intercity travel (>100km),
BlaBlaCar-style ride-sharing, private/chartered buses, and scheduled coach
services — not local/on-demand cabs (Uber/Ola city rides), which are a
different matching problem (real-time, hyper-local, already well solved).

## 2. Prior art (checked before designing, July 2026)

| Project | What it actually is | Why it isn't this |
|---|---|---|
| **Google A2A (Agent2Agent)** — Linux Foundation, 150+ member orgs | Open protocol for agent discovery ("agent cards"), capability advertisement, and task lifecycle (send task, get status, stream results) between agents | It's transport/plumbing, not a marketplace semantic. It doesn't define "offer," "negotiate," "commit," or "escrow." Intended to be built on, not competed with. |
| **Google AP2 (Agent Payments Protocol)** | Extends A2A with "Intent Mandates" and "Cart Mandates" — cryptographically signed, human-authorized spend boundaries an agent can act within without asking every time | Solves the payment-authorization half of the problem, not the negotiation half. Worth reusing directly rather than reinventing. |
| **OpenAI + Stripe Agentic Commerce Protocol (ACP)**, and the competing **UCP** | Agent-to-merchant checkout: one shopping agent buys from one seller's catalog | One-directional (buyer agent → fixed catalog). No peer negotiation between two autonomous agents representing two different parties with competing objectives. |
| **Uber × OpenAI (ChatGPT app, 2026)** + "Uber Assistant" | A conversational front-end that calls Uber's own booking API; a driver-facing assistant for earnings advice | Single-vendor UX automation. No competing provider agents, no open wire protocol, no negotiation — it's a chat skin on one company's existing backend. |
| **BlaBlaCar ML matching** | Ranks/filters/hides rides using ML ("Boost rides") | Improves the human's search results; the human still swipes/accepts/rejects manually. No agent commits on the human's behalf. |

**The gap:** no open protocol exists for two independent, self-interested
software agents — representing different companies or individuals, with
no shared backend — to discover each other, negotiate price/time/route,
and reach a binding commitment. That's the space this project is in.
Consequence for design: **build on A2A for transport/discovery and on
AP2 for the payment-mandate model, and define the missing layer —
negotiation and marketplace semantics — rather than re-doing solved parts.**

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
  app a provider chose to list on — this is the actual structural advantage
  over "just use BlaBlaCar/Uber," which are closed, single-company graphs.
- **Naturally decentralizable.** Nothing about negotiation requires a single
  central matching server; it can be a registry + direct agent-to-agent
  channel, lowering the platform's own operating leverage/lock-in over both
  sides (a deliberate contrast to how BlaBlaCar/Uber monetize via being the
  sole intermediary).

## 4. Caveats / open problems (must be designed for, not bolted on)

- **Authorization boundaries.** An agent must never be able to commit a
  human to spend or travel beyond what was explicitly authorized. Adopt
  AP2's mandate model: a signed **Intent Mandate** (what the human is
  willing to let the agent negotiate: budget ceiling, time window, max
  detour) and a signed **Commitment Mandate** the agent presents at the
  moment of binding — either pre-authorized for auto-commit within bounds,
  or requiring a final human tap.
- **Trust, identity, fraud.** Sybil provider agents, fake vehicle/capacity
  claims, agent impersonation, price collusion between provider agents.
  Needs an identity/reputation primitive in the protocol itself (signed
  agent identities + a portable reputation/attestation record), not a
  platform-side afterthought.
- **Liability and regulation.** Intercity transport is licensed (driver
  licensing, insurance, cross-border rules in some regions). "My agent
  committed me" needs an auditable, non-repudiable record of exactly what
  was authorized and agreed — this is a legal requirement, not just good
  practice.
- **Perishable inventory / race conditions.** A seat can vanish mid-negotiation.
  The protocol needs explicit **hold-with-expiry** semantics (like a payment
  auth-hold) so two consumer agents can't both believe they hold the same seat.
- **Latency vs. real-time expectations.** Negotiation implies back-and-forth
  message turns; for a ride departing in 20 minutes there may be no time for
  multi-round haggling. The protocol should support both a fast
  "take-it-or-leave-it offer" mode and a slower multi-round negotiation mode.
- **Cold-start liquidity.** A negotiation protocol has zero value with only
  one agent on each side. Plan for a simulator/testbed phase before any real
  driver/rider pilot.
- **Adverse incentives.** Provider agents optimizing purely for their own
  objective could learn to lowball then renege, or spam offers. Commitment
  needs to carry real cost (deposit/escrow-style) to keep offers meaningful.

## 5. Actors

- **Consumer Agent** — acts for the traveler. Holds preferences (route, time
  window, budget, seat count, detour tolerance, trust requirements) and an
  Intent Mandate from the human.
- **Provider Agent** — acts for a driver, small operator, or bus/coach
  service. Holds available capacity, pricing policy, and constraints (min
  passengers to run, route flexibility).
- **Registry / Discovery layer** — lets agents find each other for a given
  route/time without requiring a single central matchmaker to broker every
  deal (reuses A2A's agent-card discovery pattern). Can be run by anyone;
  the protocol doesn't require one operator.
- **Trust/Attestation service (optional, pluggable)** — issues or verifies
  identity and reputation attestations (driver verified, past-trip ratings)
  that agents can request from each other during negotiation.

## 6. Protocol layering

```
┌─────────────────────────────────────────────┐
│  Marketplace Negotiation Layer  (this repo)  │  Intent → Offer → Counter →
│                                               │  Commit → Fulfillment → Settle
├─────────────────────────────────────────────┤
│  AP2 (Agent Payments Protocol)               │  Intent/Cart Mandates,
│                                               │  payment authorization
├─────────────────────────────────────────────┤
│  A2A (Agent2Agent Protocol)                  │  agent discovery, capability
│                                               │  cards, task lifecycle, transport
└─────────────────────────────────────────────┘
```

This project defines only the top layer: what "offer," "negotiate," and
"commit" mean for a two-sided capacity marketplace, expressed as A2A task
payloads and settled via AP2 mandates. It deliberately does not reimplement
discovery or payment auth.

## 7. Core message flow

```
Consumer Agent                         Provider Agent(s)
      │                                        │
      │  1. TripIntent (broadcast/query)       │
      │ ──────────────────────────────────────>│
      │                                        │  (each matching provider
      │  2. Offer (price, time, seats, route)  │   agent evaluates its own
      │ <──────────────────────────────────────│   policy against intent)
      │                                        │
      │  3. Counter / Accept / Decline         │
      │ ──────────────────────────────────────>│
      │        ... N rounds (bounded) ...      │
      │                                        │
      │  4. Commitment (hold, expiry, mandate) │
      │ <──────────────────────────────────────│
      │                                        │
      │  5. Payment authorization (AP2)        │
      │ ──────────────────────────────────────>│
      │                                        │
      │  6. Fulfillment confirmation           │
      │ <──────────────────────────────────────│
      │                                        │
      │  7. Reputation/feedback record         │
      │ <──────────────────────────────────────│
```

Negotiation rounds are bounded (max N or a timeout) to avoid unbounded
back-and-forth; either agent can escalate to its human at any point.

## 8. Draft message schemas (illustrative, not final)

```json
// 1. TripIntent — consumer agent → registry/provider agents
{
  "type": "trip_intent",
  "intent_id": "uuid",
  "origin": {"city": "Pune", "lat": 18.52, "lng": 73.85},
  "destination": {"city": "Mumbai", "lat": 19.07, "lng": 72.87},
  "earliest_departure": "2026-07-18T06:00:00+05:30",
  "latest_departure": "2026-07-18T09:00:00+05:30",
  "seats": 1,
  "max_price_per_seat": {"amount": 600, "currency": "INR"},
  "detour_tolerance_km": 10,
  "mandate_ref": "ap2-intent-mandate-uuid"
}

// 2. Offer — provider agent → consumer agent
{
  "type": "offer",
  "offer_id": "uuid",
  "intent_id": "uuid",
  "provider_agent_id": "did:example:provider-123",
  "price_per_seat": {"amount": 550, "currency": "INR"},
  "departure": "2026-07-18T07:15:00+05:30",
  "seats_available": 2,
  "vehicle": {"type": "sedan", "verified": true},
  "hold_expires_at": "2026-07-17T15:40:00+05:30",
  "reputation_ref": "attestation-uuid"
}

// 3. Counter
{
  "type": "counter_offer",
  "offer_id": "uuid",
  "proposed_price_per_seat": {"amount": 500, "currency": "INR"},
  "proposed_departure": "2026-07-18T07:30:00+05:30"
}

// 4. Commitment
{
  "type": "commitment",
  "offer_id": "uuid",
  "status": "held | confirmed",
  "hold_expires_at": "2026-07-17T15:45:00+05:30",
  "cart_mandate_ref": "ap2-cart-mandate-uuid"
}
```

## 9. Scope for v0 (what to actually build first)

1. **Spec only, no real money/drivers.** Define the negotiation message
   schema and state machine precisely (this doc → formal schema files).
2. **Simulator.** Scripted consumer and provider agents that negotiate over
   synthetic trip intents, to validate the protocol handles: multi-round
   negotiation, hold expiry/races, decline/timeout paths, and bounded
   negotiation rounds — before any real user is involved.
3. **Reference implementation** of both agent roles as a thin layer over an
   A2A SDK, with AP2 mandate objects stubbed (structurally correct, not
   wired to a real payment processor yet).
4. **Single narrow pilot route** (e.g. one intercity corridor) with real but
   consenting drivers, manual fallback for anything the protocol doesn't
   yet cover, before generalizing to other verticals.

## 10. Explicitly out of scope for now

- Local/on-demand city rides (different problem, well-served already).
- Cross-border regulatory/licensing handling.
- A proprietary central matching engine — the point is agents negotiating
  directly, not another closed platform in the middle.
