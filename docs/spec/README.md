# The spec: an OS for agent-mediated marketplaces

This folder is the **authoritative, buildable design** — the point where
the exploration in `../design.md`, `../industries/`, `../technical-deep-
dive/`, `../core-model/`, `../business-strategy/`, and `../platform-
architecture/` collapses into one frozen picture we can ship against.

It is written around ten founding principles captured directly from the
project author's design notes (transcribed verbatim in `01`), and it
resolves the places where those notes *change* earlier conclusions rather
than just adding to them.

## The framing: a marketplace OS, for humans and agents alike

We are not building a ride app or a services app. We are building the
**operating system for any two-sided marketplace that matches demand to
supply** — where the participants may be autonomous agents *or* humans, and
where the marketplace itself can be **plugged into any distribution
platform** (Uber, Zomato, OLX, Meesho, …) as a layer on top of what they
already run.

A human is treated as a **special case of an agent** — an agent whose
`autonomy_level` is "confirm everything," a human in the loop on every
decision. The agent interface is the canonical one; the human UI is just
the fully-supervised mode of it. This is what "serving humans or agents"
means concretely: one protocol, two levels of autonomy.

## Files

| # | File | What it gives you |
|---|---|---|
| 1 | [`01-principles-and-lifecycle.md`](01-principles-and-lifecycle.md) | The ten principles, formalized (and where each one changes prior docs), plus the **complete end-to-end lifecycle** of a single transaction — the "how does the whole process actually work" you asked for. |
| 2 | [`02-layers-governance-security.md`](02-layers-governance-security.md) | The four-layer responsibility model — **protocol / operator / governance / security-and-fraud** — so it's unambiguous who owns ranking, trust, dispute resolution, Sybil resistance, and money. Answers "what are we doing with the governance layer, security, fraud prevention." |
| 3 | [`03-mvp-build-scope.md`](03-mvp-build-scope.md) | The **frozen v0 scope** — exactly what we build first, what we deliberately leave out, and the reference-build plan. This is the "decide what to build" artifact. |

## The three decisions from the notes that change earlier docs

Called out here so nothing is silently contradicted:

1. **Providers cannot collaborate; consumers can** (principle 1). This
   makes the *symmetric* `Coalition` from `../core-model/01-entities.md`
   **asymmetric by default**: consumer-side coalition is a first-class
   protocol capability; provider-side bundling is disabled by default and
   only ever enabled as a disclosed, governance-gated exception (it is the
   exact structure collusion needs — `../design.md` §7). See `01` §P1.
2. **Grouping keys ≠ constraints ≠ preferences** (principle 3). A clean
   three-tier data model that sharpens `../core-model`'s
   `market_key`/`constraints`/`category_ext`. See `01` §P3.
3. **Ranking belongs to the network operator, not the protocol**
   (principle 10). The protocol supplies mechanism (grouping, queuing,
   matching state machine, negotiation, escrow); the operator supplies the
   ranking/scoring policy. See `01` §P10 and `02` Layer B.
