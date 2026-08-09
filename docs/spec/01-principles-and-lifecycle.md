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

### P11 — "Provider and customer messages go to different queues. Fraudulent ones are filtered before entering the matching pool. First-order match → staging → notify parties → each party puts money in → commit (an agreement, not the final step) → after both approve + platform verifies evidence → complete."

**Rule — two queues, a pre-pool fraud gate, and a staging phase before
commitment.** Refines P4, P6, P7, and P8 with three concrete mechanisms
added by these notes:

1. **Separate demand and supply queues, per partition.** Not one merged
   queue — a `DemandQueue` and a `SupplyQueue`, both keyed by the same
   grouping-key partition (P3), matched *between* the two. This is a
   clarification of the existing FIFO design (P6), not a change to it.
2. **Per-request fraud/governance filtering happens before pool entry, not
   only at onboarding.** P4's identity gate (Stage 0) checks the *agent*
   once; this adds a second, per-*request* filter (Stage 1.5) that runs on
   every `Intent`/`Offer` before it's admitted to a queue — catching a
   verified agent that starts spawning fraudulent requests after
   onboarding, which a one-time identity check can't. See `02` Layer D.
3. **A match is a proposal, not an instant commitment.** A first-order
   match does not immediately form a binding `Commitment`. It creates a
   **staged match proposal**, both parties are notified, and **both must
   explicitly approve and have funds captured** (consumer payment, and —
   where the category requires it — a provider stake/deposit) before the
   `Commitment` exists at all. Forming a `Commitment` is therefore already
   "agreement reached, funds in platform custody" — **not** the final
   step. Money is held in **platform custody** (the operator, not a
   third-party clearing exchange) until the separate, later P8
   dual-approval-plus-evidence gate releases it. This inserts one real new
   stage into the lifecycle (Stage 6a below) that P7/P8 previously
   compressed into one step.

### P12 — "Demand requests wait a fixed period, then move to a collaboration queue where negotiation starts. A joint offer can pull in new supply."

**Rule — time-boxed escalation, not immediate escalation.** P5 said
"collaborate on failure"; this specifies *when* failure is declared: each
`Intent` carries a wait duration. While that timer runs, only solo
matching is attempted. **Only once it expires** does the intent move from
the demand queue into a **collaboration/negotiation queue**, where
coalition formation (P1, P5) is attempted. This makes the demand queue and
the collaboration queue two distinct, sequential pools, not one queue with
an inline fallback.

**"A joint offer can create new suppliers."** The aggregated demand
signal sitting in the collaboration queue isn't only matched against
*existing* offers — it can be **published as a demand signal that induces
new supply** (a provider agent that wasn't planning to serve this
partition sees enough pooled demand to make it worthwhile and posts a new
`Offer` in response). The collaboration queue is a demand-signal broadcast
point, not just a passive coalition-matching pool.

### P13 — "Supply/demand imbalance across networks; oversupply must never be fixed by pressuring demand; services have wildly different durations, and disputes can happen mid-service. Network-layer foundations for both are needed."

Two distinct problems, each substantial enough for its own doc:

- **Supply/demand imbalance and the anti-manipulation stance** — worked
  through fully in
  [`04-supply-demand-balance.md`](04-supply-demand-balance.md).
- **Variable service duration and mid-fulfillment disputes** — worked
  through fully in
  [`05-disputes-and-variable-duration.md`](05-disputes-and-variable-duration.md).

---

## Part B — The complete lifecycle (end to end)

The process you were unsure about, as one continuous flow. Every stage
names the principle(s) it implements.

```
 STAGE 0  ONBOARDING & IDENTITY
   participant (human or agent) joins → gets a DID, attestations
   → Sybil/fraud checks at entry (P4)                          ── security gate
        │
        ▼
 STAGE 1  REQUEST SUBMISSION
   demand agent submits Intent  |  supply agent posts Offer
   each carries: grouping keys + constraints + preferences (P3)
        │
        ▼
 STAGE 1.5  PER-REQUEST FRAUD FILTER (P11, P4)                 ── security gate
   fraudulent/manipulated requests rejected HERE — before
   admission to any queue, not after
        │
        ▼
 STAGE 2  PARTITION → TWO QUEUES (P11)
   DemandQueue[partition]      SupplyQueue[partition]
   both keyed by grouping keys (P3), both FIFO-ordered (P6)
        │                            │
        ▼                            ▼
 STAGE 3  FIRST-ORDER (SOLO) MATCH               ◀── ranking = operator policy (P10)
   filter DemandQueue × SupplyQueue by hard constraints
   → rank by preferences → try earliest-queued compatible pair
        │
        ├──── match found ──────────────────────────────┐
        │                                                │
        ▼ no match before this intent's wait timer        │
        │ expires (P12)                                   │
 STAGE 4  ESCALATE TO COLLABORATION QUEUE (P12, P5)        │
   intent moves DemandQueue → CollaborationQueue           │
   → attempt CONSUMER coalition formation (P1: demand      │
   only) → pooled demand signal may also induce NEW        │
   supply to be posted (P12)                               │
        │                                                │
        ▼                                                │
 STAGE 5  OFFER / NEGOTIATION                              │
   demand (solo or coalition) ↔ provider negotiate         │
   via the mechanism (FIFO-bilateral default)              │
   providers never negotiate jointly (P1)                  │
        │                                                │
        ▼                                                │
 STAGE 6  MATCH PROPOSED  ◀───────────────────────────────┘
   a staged proposal — NOT yet a Commitment (P11)
   both parties notified
        │
        ▼
 STAGE 6a  DUAL APPROVAL + FUNDS CAPTURED (P11)
   consumer approves  AND  provider approves
   (auto-approved instantly if that side's Mandate.autonomy_level
   allows auto-commit within scope, mandate ceiling enforced in
   code — P4/P8)
   → funds captured into PLATFORM CUSTODY (not a third-party
   exchange) — consumer payment, and provider stake if the
   category requires one
        │
        ├──── either side declines/times out ──▶ proposal EXPIRES,
        │                                          demand re-queued
        ▼
 STAGE 6b  COMMITMENT FORMED (P7)
   this is AN AGREEMENT, explicitly not the final step —
   escrow.state = held, in platform custody
        │
        ▼
 STAGE 7  FULFILLMENT WINDOW (P13 — variable duration:
   1 minute to multiple days, see 05-disputes-and-
   variable-duration.md)
   service performed; a DISPUTE may be raised by either
   party AT ANY POINT during this window, not only at the end
        │
        ├──── dispute raised ───────────────────▶ DISPUTE HANDLING
        │                                          (05, 02 Layer C)
        ▼ no dispute raised
 STAGE 8  DUAL APPROVAL + VERIFICATION (P8)
   consumer approves completion AND provider approves completion
   AND platform verifies completion via evidence/trace logs
        │
        ├──── all three pass ──▶ STAGE 9  SETTLEMENT
        │                          escrow released to provider
        │                          minus thin protocol fee
        │                          → ratings recorded (fraud-checked, P4)
        │
        └──── any fail ────────▶ DISPUTE RESOLUTION (05, 02 Layer C)
                                   adjudicated on the audit trail
```

Read top to bottom, this is the whole marketplace OS in one column: a
request is fraud-checked and queued fairly on its own side (demand vs.
supply), tries to match solo, escalates to consumer collaboration only
after its own wait timer expires, negotiates, gets *proposed* as a match
rather than instantly bound, requires both sides' explicit approval and
captured funds before it becomes a real `Commitment` (an agreement, not
completion), runs through a fulfillment window of whatever length the
service actually takes — open to a dispute at any point in that window —
and only releases money after both-side approval plus independent
platform verification. Everything participant-specific (preferences,
ranking) is applied inside this flow by the *operator*; the protocol just
runs the machine.
