# Four layers: protocol, operator, governance, security

You said you're unsure what we're doing with the governance layer,
security, and fraud prevention. The clean answer is a **four-layer
responsibility model** where every concern has exactly one owner. If you
remember one thing: **the protocol is deliberately dumb and neutral; all
the judgment lives in the layers above it.**

```
┌──────────────────────────────────────────────────────────────┐
│  LAYER D — SECURITY & FRAUD PREVENTION   (cross-cutting)       │
│  Sybil resistance · rating-manipulation defense · prompt-      │
│  injection defense · escrow/evidence anti-fraud · collusion    │
│  detection. Touches every layer below.                         │
├──────────────────────────────────────────────────────────────┤
│  LAYER C — GOVERNANCE          (neutral / foundation)          │
│  trust framework · conformance certification · category        │
│  registration · dispute adjudication rules · anti-collusion    │
│  monitoring · safety-critical floors                           │
├──────────────────────────────────────────────────────────────┤
│  LAYER B — NETWORK OPERATOR    (the distribution platform)     │
│  RANKING/scoring · which categories · business policy ·        │
│  autonomy defaults · UX/distribution · their fee               │
├──────────────────────────────────────────────────────────────┤
│  LAYER A — PROTOCOL CORE       (neutral, minimal, dumb)        │
│  grouping · FIFO queue · match/negotiate/commit/escrow state   │
│  machine · wire format · identity · settlement primitive       │
└──────────────────────────────────────────────────────────────┘
```

## Layer A — Protocol core (mechanism only)

**Owns:** the grouping rule (P3), FIFO queuing (P6), the
match→negotiate→commit→escrow→settle state machine (P5–P8), the wire
message format, DID identity, and the escrow/settlement *primitive*.

**Deliberately does NOT own:** ranking (that's B, per P10), price-setting,
which categories run, or any business policy. The protocol is a neutral
referee that runs the machine and enforces the rules of the game — it never
picks winners. This neutrality is what lets competitors co-adopt it
(`../platform-architecture/04`) and what keeps it from becoming "another
platform."

## Layer B — Network operator (policy & distribution)

**Owns (per P9, P10):**
- **Ranking/scoring** — how providers (or demand) are ordered within the
  filtered candidate set. This is pluggable operator policy; the protocol
  hands the operator the eligible, constraint-passing candidates and the
  operator's own ranking function decides order. Uber-the-deployer can rank
  by ETA, OLX-the-deployer by price, another by their own strategy — all
  conformant. "Flexible and agile" (P10) lives here.
- **Category selection**, autonomy defaults (within governance floors),
  their own fee on top of the protocol fee, and the consumer/provider UX
  their users actually see.

**Why it's a separate layer:** the operator brings distribution and
category expertise (`../business-strategy/06`); forcing them to accept the
protocol's ranking would make it un-adoptable. Mechanism is universal;
policy is theirs.

## Layer C — Governance (neutral trust & rules)

**Owns the things that must be neutral to be trusted:**
- **Trust framework** — which identity/attestation issuers are recognized
  (`../platform-architecture/03` §4), the root of Sybil resistance.
- **Conformance certification** — who is a compliant network/agent
  (`../platform-architecture/04` §5); the anti-fragmentation lever.
- **Category registration governance** — approving `ServiceCategory`
  definitions and their safety floors (e.g., home-healthcare's no-silent-
  auto-commit floor, `../industries/home-healthcare.md`).
- **Dispute adjudication rules** — the defined process when Stage 8
  verification fails; adjudicated on the audit trail.
- **Anti-collusion monitoring** — watching for correlated provider pricing
  even though providers can't formally collaborate (P1 removes the easy
  path; monitoring catches the tacit/algorithmic path, `../design.md` §7).
- **Approving any P1 exception** — the disclosed supply-side-coalition
  cases only exist if governance grants them.

**Who runs it:** starts operator/company-led, moves toward a neutral
foundation as it matures (`../platform-architecture/04` §4). This is the
layer whose *neutrality is the whole product* on the managed side
(`../business-strategy/06`).

## Layer D — Security & fraud prevention (cross-cutting)

Not a layer you "add later" — it threads through A, B, and C. This directly
answers principle **P4**. The named threats and their controls:

| Threat | Control | Which layer enforces |
|---|---|---|
| **Sybil / fake-request flooding** (P4) | Identity cost proportional to vertical risk (`../technical-deep-dive/06` §4); DID + attestation gate at onboarding (Stage 0); rate limits per verified identity | A (identity) + C (trust framework) + B (per-category threshold) |
| **Rating/reputation manipulation** (P4) | Ratings only from *verified completed* commitments (a rating must reference a settled escrow — no transaction, no rating); anomaly detection on rating patterns; reputation carries provenance (`../platform-architecture/03` §4) | A (rating-requires-settlement rule) + C (anomaly monitoring) |
| **Prompt injection between agents** (`../technical-deep-dive/06` §3) | Strictly typed wire format (no free-text instructions crossing the wire); mandate limits enforced in code, not LLM reasoning | A (typed protocol) |
| **Payment/completion fraud** (fake "it's done") | Escrow + dual approval + independent evidence verification (P8); money never moves on one party's say-so | A (escrow primitive) + B (evidence adapters) |
| **Tacit/algorithmic price collusion** (providers can't formally collude, P1, but pricing can still correlate) | Anti-collusion monitoring on cleared prices vs. reference band; quarantine flagged providers | C (monitoring) |
| **Bad-actor networks (in federation)** | Defederation + certification gate (`../platform-architecture/03` §6) | C (governance) |

**The design stance:** put as much fraud resistance as possible into
*structural* controls at Layer A (typed messages can't carry injection;
escrow can't release without evidence; a rating can't exist without a
settled transaction) so that fraud is *impossible by construction* where
feasible, and only fall back to *detection* at Layer C (monitoring,
anomaly detection) where structure can't prevent it. Structural prevention
beats detection wherever you can get it.

## The one-line mental model

**Layer A runs the machine and can't be evil (it's neutral and dumb).
Layer B decides who wins (ranking) and how it looks (UX). Layer C decides
who's allowed to play and settles fights (trust, certification, disputes).
Layer D makes sure nobody cheats, structurally where possible and by
detection where not.** Every concern you were unsure about maps to exactly
one of these four owners.
