# Disputes and variable-duration fulfillment: the network-layer foundation

The notes are explicit about scope here: **not the actual dispute policy**
(how much to refund, who's at fault) — that is Layer C, operator/
governance territory (`02-layers-governance-security.md`). This doc is the
**network-layer foundation** every operator's policy sits on: the states,
transitions, and guarantees the protocol itself provides, applicable to
any distribution using it, regardless of what their specific dispute rules
say.

## 1. The problem: fulfillment is a window, not an instant

Every earlier version of the lifecycle (`01-principles-and-lifecycle.md`
Part B, and the original `../design.md`) treated fulfillment as
effectively a single event: service happens, then dual approval + evidence.
That's wrong for most of the real verticals this protocol targets — a food
delivery might complete in 15 minutes, a home-services repair in 2 hours, a
freight haul in 10 hours, an event booking's actual "service" spans days.
**Fulfillment must be modeled as a window with a start and an
expected/actual end, not a point in time**, and — critically — **a dispute
can be raised by either party at any point inside that window**, not only
after the fact.

## 2. The state machine (network layer, applies to every category)

```
Commitment formed (escrow: held, platform custody)
        │
        ▼
 FULFILLMENT WINDOW OPEN
   start_at recorded; expected_end derived from the category
   (a fixed instant for a 15-min delivery, a multi-day span for
   a renovation — the WINDOW LENGTH is category data, never a
   protocol constant)
        │
        ├── no dispute, window completes normally ──▶ STAGE 8
        │                                              (dual approval +
        │                                               evidence, as before)
        │
        └── DISPUTE RAISED (either party, any time in window)
                │
                ▼
         escrow.state → DISPUTED (frozen: not released to
         EITHER party, not refunded, not partially paid, until
         resolved — the one hard guarantee the protocol makes)
                │
                ▼
         audit trail snapshotted (all messages, evidence-to-date,
         checkpoint records — see §4 — up to the dispute moment)
                │
                ▼
         handed to the governance-layer DisputeResolver (Layer C,
         `02`) — the protocol does not decide outcomes, only
         guarantees the trail and the freeze
                │
                ▼
         RESOLUTION — closed set of terminal outcomes the
         protocol defines the SHAPE of (§5), the CONTENT of which
         is the operator's policy
                │
                ▼
         escrow moves to one of: released (to provider),
         refunded (to consumer), or partially both — per the
         resolution — never anything outside this closed set
```

## 3. Why this must be a protocol-level guarantee, not left to each operator

Two things have to be true *regardless* of which operator is running the
network, or cross-network federation (`../platform-architecture/03`)
becomes unworkable — a dispute spanning a federated transaction needs both
sides' networks to agree on what "disputed" means structurally:

- **The freeze is unconditional.** The instant a dispute is raised, no
  further money movement happens until resolution — not even a favorable-
  looking partial release — because allowing one side's claim to
  pre-emptively move funds defeats the point of having a dispute state at
  all.
- **The audit trail is preserved, not just available.** Every message,
  approval, and evidence record up to the dispute point is a durable,
  non-repudiable snapshot (building on the signature/audit design already
  in `../core-model/01-entities.md` and `../technical-deep-dive/07` §6) —
  this is what makes disputes *adjudicable* rather than a pure he-said/
  she-said, and it's a protocol guarantee because a resolver (human,
  automated, or a federated peer network's resolver) can't adjudicate what
  wasn't preserved.

## 4. Checkpoints: making long-duration services disputable *and* partially settleable

A single end-of-window evidence check (as the original P8 design assumed)
is fine for a 15-minute delivery and inadequate for a 2-day job — if a
dispute happens on day 1 of a 2-day renovation, "no evidence exists yet"
shouldn't mean "no partial credit is possible." The network-layer answer:

- **Checkpoint evidence is category-defined, not protocol-fixed.** A
  category may declare zero, one, or many checkpoints across the
  fulfillment window (a `Category.checkpoint_schedule` concept alongside
  the existing `verify_evidence` hook, `../core-model/01-entities.md`
  §10). A 15-minute delivery category declares none (single end check,
  today's behavior); a multi-day category declares milestone checkpoints.
- **A checkpoint that has been reached and evidenced becomes part of the
  audit trail available to dispute resolution**, enabling **partial
  settlement** as a legitimate resolution outcome (§5) — "60% of the
  agreed work was checkpoint-verified before the dispute" is now a fact
  the resolver can act on, rather than an unanswerable claim. This is the
  network-layer hook; whether a given operator's policy actually grants
  partial payment for partial checkpoints is their Layer C decision.

## 5. The closed set of terminal outcomes (shape, not policy)

The protocol defines the *vocabulary* of what a dispute can resolve to —
this bounds what any operator's policy is allowed to produce, without
telling them which one to pick for a given case:

| Outcome | Escrow effect |
|---|---|
| `full_release` | 100% to provider (dispute found in provider's favor / withdrawn) |
| `full_refund` | 100% back to consumer |
| `partial` | split, informed by checkpoint evidence where available (§4) |
| `escalated` | held further, referred beyond the network's own resolver (e.g. external arbitration, or — for a federated transaction — the counterpart network's resolver) |

No operator implementation may invent a fifth kind of terminal state that
sits outside this set (e.g., "money quietly returned to the platform's own
account" is not a valid outcome) — this closed set is itself part of the
protocol-layer guarantee, precisely because it's the thing federation and
cross-network trust (`../platform-architecture/03` §5-6) depend on being
predictable.

## 6. What stays explicitly out of scope here (Layer C's job)

- The actual rules for *deciding* fault or the specific split percentage.
- Who acts as the human/automated resolver, and their qualification/
  certification (`../platform-architecture/04` §5's conformance
  machinery is one credible way to gate this, but that's an operator/
  governance choice, not specified here).
- SLA definitions (what counts as "late," what counts as "checkpoint
  missed") — category- and operator-specific.

This doc's only job is the state machine, the freeze guarantee, the audit
trail requirement, the checkpoint hook, and the closed outcome vocabulary
— the foundation "applicable to all kinds of distributions," per the
notes, that every operator's actual policy is built on top of.
