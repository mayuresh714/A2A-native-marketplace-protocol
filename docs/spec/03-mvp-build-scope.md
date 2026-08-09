# v0 build scope (frozen)

Enough discussion. This is the smallest thing that exercises the whole
lifecycle (`01` Part B) end to end and proves the idea is real, with
everything speculative deliberately cut. Anything not listed as IN is OUT
of v0 — that's the point of freezing scope.

## 1. What v0 is

**A single-network, single-vertical, in-simulation reference
implementation of the core lifecycle** — one operator, no federation, one
category, scripted agents, fake money. It proves the machine runs
end-to-end before any real user, driver, or rupee is involved (the same
"simulator before pilot" discipline from `../design.md` §13).

**Reference vertical: intercity ride-pooling.** Every worked example in the
repo already uses it (`../design.md` §5's Pune–Kolhapur pooling), it scores
8/8 on market fit (`../business-strategy/02`), and it exercises the one
hard, differentiating feature (consumer collaboration) that a trivial
vertical wouldn't. Grouping keys: `(source_region, destination_region,
start_time_bucket)`.

## 2. IN scope for v0

**Entities (minimal subset of `../core-model/01-entities.md`):**
`Agent`, `Intent`, `Offer`, `Commitment`, `Fulfillment`, `Mandate`,
`Attestation` (minimal), `Market`/partition. Deferred: full
`ClearingMechanism` taxonomy, `Negotiation` as a heavy object (v0
negotiation is a bounded bilateral exchange), standing `Coalition`.

**The lifecycle, exactly these stages:**
- Onboarding with DID + a minimal attestation gate (P4 Sybil floor).
- Request submission with the **three-tier split** — grouping keys /
  constraints / preferences (P3).
- Partition + **FIFO queue** within partition (P6).
- **Solo-first match**, ranked by an operator-supplied ranking function
  (P10 — v0 ships one simple default ranking function, but as a swappable
  policy interface, not hardcoded into the core).
- **On failure: consumer coalition formation** (P1 demand-side only; P5
  failure-triggered) — the marquee feature, using the time-interval-overlap
  + additive-price aggregation from `../technical-deep-dive/02` §4.
- Bounded **bilateral negotiation** (no auctions).
- **Commitment → escrow** (P7, P8).
- **Fulfillment → dual approval + evidence verification → settlement**
  (P8), with a stubbed evidence check (e.g. a simulated GPS drop-confirm).
- Ratings **only from settled commitments** (P4 anti-manipulation
  structural rule).

**Security, structural only (Layer D, `02`):** typed wire format (no
free-text instruction fields → prompt-injection-resistant by construction),
escrow-can't-release-without-evidence, rating-requires-settlement. Detection
/ monitoring is deferred.

**Deliverable shape:** a runnable simulator that spins up N demand agents
and M supply agents with scripted preferences over synthetic intercity
demand, runs the full lifecycle, and reports outcomes (match rate, coalition
formation rate, settlement rate, dispute rate) — plus the frozen wire
schemas (`../core-model/04-schema.md` subset) the agents speak.

## 3. OUT of v0 (explicitly deferred, not forgotten)

- **Federation / network-of-networks** (`../platform-architecture/03`) —
  v0 is one island.
- **Auctions & combinatorial clearing** (`../technical-deep-dive/04`) —
  FIFO bilateral only; auctions are a later operator upgrade (P6
  reconciliation).
- **Provider-side coalitions** (P1) — disabled; the governed exception
  isn't built until governance exists.
- **Real payment rails** — escrow and settlement are simulated; AP2/UPI
  adapters come after the machine is proven.
- **Sophisticated anti-collusion monitoring** (Layer C) — structural
  prevention only in v0; detection later.
- **Multiple verticals, multi-currency, cross-border** — one vertical, one
  currency, one region.
- **The managed control plane / NaaS productization** (`../platform-
  architecture/02`) — that's a business-stage concern, not a
  prove-the-idea concern.

## 4. Build order within v0

1. **Freeze the wire schemas** for the v0 entity subset (typed, versioned).
   This is the contract everything else is written against.
2. **Implement the core state machine** (Layer A): partition + FIFO queue +
   solo match + coalition-on-failure + bilateral negotiate + escrow +
   settle. Neutral, no ranking policy inside it.
3. **Implement one swappable ranking policy** (Layer B interface, one
   default impl) so the mechanism/policy boundary (P10) is real from day
   one, not retrofitted.
4. **Build the simulator harness** — scripted agents, synthetic intercity
   demand generator, metrics output.
5. **Run it, read the metrics, iterate the protocol** where the simulation
   exposes gaps (hold-expiry races, coalition-timeout fallback,
   dispute-path correctness — the exact things `../technical-deep-dive/01`
   §3 and `02` warned about).

The success test for v0: **the simulator reliably takes a batch of
individually-unmatchable intercity requests and, through solo-first +
consumer-coalition-on-failure + escrowed settlement, produces more
completed, evidence-verified transactions than a naive bilateral-only
matcher on the same demand** — with zero money released without dual
approval + evidence. If it does that, the idea is proven and the next
stage (real payment adapter, then a narrow real pilot) is justified. If it
doesn't, we learned it cheaply, in simulation, before shipping anything
real.

## 5. What "shipping today" means concretely

Two candidate first commits of actual code, in dependency order:

- **(a) Frozen v0 wire schemas** — the typed entity/message definitions
  (JSON Schema) for the subset in §2. Everything else depends on these, so
  they're the natural first real artifact.
- **(b) The simulator skeleton** — the harness + core state-machine stubs
  that the schemas plug into.

Both are small, concrete, and move the repo from all-docs to
first-code. The recommendation is to do (a) then (b). The two open choices
that are genuinely yours to make — the reference vertical and the first
build target — are put to you directly rather than assumed.
