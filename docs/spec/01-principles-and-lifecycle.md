# The ten principles, and the complete lifecycle

## Part A — The ten principles (verbatim, then formalized)

Transcribed from the design notes, then each turned into a concrete design
rule with its impact on the rest of the repo.

### P1 — "Consumers can collaborate with themselves, but service providers cannot."

**Rule.** Consumer-side (demand-stance) collaboration is a first-class
protocol capability. Provider-side (supply-stance) collaboration is
**disabled by default.**

**Why this is right, not just a preference.** Provider-to-provider
coordination *is* the structural definition of a cartel
(`../design.md` §7, `../technical-deep-dive/03`). Forbidding it by default
removes the collusion surface at the protocol level instead of trying to
detect it after the fact. Consumers pooling to get a better deal is
pro-competitive; providers pooling to set terms is anti-competitive — the
asymmetry is the point.

**What it changes.** The `Coalition` entity in `../core-model/01-
entities.md` §7 was described as *symmetric* (demand- or supply-side, same
object). It is now **asymmetric by default**: `Coalition.stance` may be
`demand` freely; `stance = supply` is a governance-gated, must-be-disclosed
exception a network operator can enable per-category only with explicit
antitrust/disclosure controls (the event-vendor and freight-bundling cases
in `../industries/` move from "core capability" to "governed exception").

### P2 — "A protocol/system pluggable into any distribution platform (Uber, Zomato, OLX, Meesho)."

**Rule.** The protocol is a layer that mounts on top of an existing
distribution platform, not a standalone app. Already the whole thesis of
`../platform-architecture/` — this principle confirms the direction. See
also P9.

### P3 — "We need keys on which both sides' requests can be grouped (source, destination, start time for carpooling). User/provider-specific constraints should NOT be part of this."

**Rule — the three-tier data model.** Every request (demand or supply)
separates into three tiers, and only the first is used to *group/match*:

| Tier | What it is | Used for | Example (carpooling) |
|---|---|---|---|
| **Grouping keys** | Minimal, shared, category-defined coarse dimensions | Partitioning requests into the same matchable pool (the `Market` shard) | source, destination, start-time bucket |
| **Constraints** | Hard requirements that must be satisfied | Filtering candidates *within* a pool | seats needed, budget ceiling, hard latest-departure |
| **Preferences** | Soft, individual desires | Ranking within the filtered set, and triggering collaboration on failure (P5) | comfort prefs, provider quality, exact timing |

**Why.** If user/provider-specific constraints were part of the grouping
key, every request would land in its own partition of one and nothing
would ever match. Grouping keys must be coarse and shared so a pool
actually forms; individuality is applied *later*, as filters and ranking.
This sharpens `../core-model`'s `market_key` (= grouping keys) vs.
`constraints` vs. `category_ext`/preferences — same idea, now a hard rule:
**grouping keys are coarse and category-owned; nothing participant-specific
is ever a grouping key.**

### P4 — "There will be fraudulent entities spawning fake requests and manipulating ratings on both sides. Prevention mechanisms required."

**Rule.** Fraud prevention is a first-class, mandatory layer, not a
feature. Two named threats from the notes — **Sybil/fake-request flooding**
and **rating manipulation** — plus the ones already in the repo (prompt
injection, `../technical-deep-dive/06` §3). Fully specified in `02` Layer D.

### P5 — "Collaboration is step 2. First: individual matching by preferences. Constraints/collaboration come in at time of failure to get a first-order match."

**Rule — solo-first, collaborate-on-failure.** The matching engine always
attempts an individual (solo) match first, ranked by preferences. Only when
a request *fails* to get a good first-order match does it escalate:
progressively relax soft preferences, then attempt consumer coalition
formation (P1). Collaboration is a fallback that unlocks otherwise-dead
requests, never the default path. Confirms and elevates the
failure-triggered coalition design in `../technical-deep-dive/02`.

### P6 — "Requests queued FIFO; earlier ones within a partition/group get more priority."

**Rule.** Within a partition (grouping-key bucket), the default ordering is
**FIFO — first-come, first-served.** Earlier requests are matched first.
This is the fairness default and the primary matching mode.

**Reconciliation with the auctions in `../technical-deep-dive/04`.** FIFO
continuous matching is the **default** mode for normal/thin liquidity. The
sealed-bid/auction mechanisms are an **opt-in batch mode** a network
operator may enable for thick, schedulable partitions — they are not the
default and are out of v0 scope (`03`). No contradiction: FIFO is the base
case, auctions are an operator upgrade.

### P7 — "Transaction happens when a provider('s) request is fulfilled by a demand request."

**Rule.** A `Commitment` forms at the moment a supply request's capacity is
matched-and-agreed against a demand request. "Transaction" = a formed,
mutually-agreed commitment — the trigger for escrow (P8).

### P8 — "Money exchanges only when consumer AND provider approve completeness, and the platform verifies it with trace logs/evidences."

**Rule — escrow with dual approval + evidence verification.** Funds are
**held in escrow** at commitment, and released **only** when: (a) the
consumer approves completion, (b) the provider approves completion, and
(c) the platform independently verifies completion against trace
logs/evidence (GPS, delivery confirmation, signed job-done, etc.). Any of
the three failing routes to dispute resolution (`02` Layer C). This makes
the audit trail load-bearing, not decorative — the same records that make
disputes cheap (`../technical-deep-dive/07` §6) are the release condition.

### P9 — "The network operator (distribution platform) can create or adjust it to their existing utility; the protocol is a layer on top of existing platforms."

**Rule.** The operator adapts the protocol into their stack; the protocol
does not dictate their product. Reinforces the deployer-owned Layer 3 of
`../platform-architecture/01` and the deployment topologies of `02` there.

### P10 — "Ranking providers is the network operator's job, NOT the protocol layer. Everything flexible and agile."

**Rule — mechanism vs. policy separation.** The protocol owns *mechanism*:
grouping, FIFO queuing, the match/negotiation/escrow state machine. The
**ranking/scoring function is operator-owned pluggable policy**, explicitly
outside the protocol core. Two operators on the same protocol can rank
providers completely differently (one by price, one by quality, one by
their own strategic goals) and both are conformant. This is the single
sharpest boundary in the whole design and is formalized as Layer B in `02`.

---

## Part B — The complete lifecycle (end to end)

The process you were unsure about, as one continuous flow. Every stage
names the principle(s) it implements.

```
 STAGE 0  ONBOARDING & IDENTITY
   participant (human or agent) joins → gets a DID, attestations
   → Sybil/fraud checks at entry (P4)                         ── security gate
        │
        ▼
 STAGE 1  REQUEST SUBMISSION
   demand agent submits Intent  |  supply agent posts Offer
   each carries: grouping keys + constraints + preferences (P3)
        │
        ▼
 STAGE 2  PARTITION & QUEUE
   placed into the partition defined by grouping keys (P3)
   ordered FIFO within the partition (P6)
        │
        ▼
 STAGE 3  FIRST-ORDER (SOLO) MATCH               ◀── ranking = operator policy (P10)
   filter by hard constraints → rank by preferences
   → try to match earliest-queued compatible pair (P6)
        │
        ├──── match found ─────────────────────────────┐
        │                                               │
        ▼ no good match                                 │
 STAGE 4  ESCALATE (only on failure) (P5)               │
   relax soft preferences → then attempt CONSUMER        │
   coalition formation (P1: consumers may pool;          │
   providers may not) → form a joint demand              │
        │                                               │
        ▼                                               │
 STAGE 5  OFFER / NEGOTIATION                            │
   demand (solo or coalition) ↔ provider negotiate       │
   via the mechanism (FIFO-bilateral default)            │
   providers never negotiate jointly (P1)                │
        │                                               │
        ▼                                               │
 STAGE 6  COMMITMENT / TRANSACTION  ◀────────────────────┘
   provider capacity fulfilled by demand (P7)
   → Commitment formed → funds AUTHORIZED & moved to ESCROW (P8)
        │
        ▼
 STAGE 7  FULFILLMENT
   service delivered → trace logs / evidence collected (P8)
        │
        ▼
 STAGE 8  DUAL APPROVAL + VERIFICATION (P8)
   consumer approves  AND  provider approves
   AND platform verifies completion via evidence
        │
        ├──── all three pass ──▶ STAGE 9  SETTLEMENT
        │                          escrow released to provider
        │                          minus thin protocol fee
        │                          → ratings recorded (fraud-checked, P4)
        │
        └──── any fail ────────▶ DISPUTE RESOLUTION (02 Layer C)
                                   adjudicated on the audit trail
```

Read top to bottom, this is the whole marketplace OS in one column: a
request comes in, gets grouped and queued fairly, tries to match solo,
escalates to consumer collaboration only if it must, negotiates, commits
into escrow, is fulfilled, is verified from both sides plus evidence, and
only then does money move — with fraud checks at entry and at rating, and a
dispute path when verification fails. Everything participant-specific
(preferences, ranking) is applied inside this flow by the *operator*; the
protocol just runs the machine.
