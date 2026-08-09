# The spec: an OS for agent-mediated marketplaces

This folder is the **authoritative, buildable design** — the point where
the exploration in `../design.md`, `../industries/`, `../technical-deep-
dive/`, `../core-model/`, `../business-strategy/`, and `../platform-
architecture/` collapses into one frozen picture we can ship against.

It is written around thirteen founding principles captured directly from
the project author's design notes (transcribed verbatim in `01`), and it
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
| 1 | [`01-principles-and-lifecycle.md`](01-principles-and-lifecycle.md) | The thirteen principles, formalized (and where each one changes prior docs), plus the **complete end-to-end lifecycle** of a single transaction — dual demand/supply queues, a per-request fraud filter, a staged match-proposal step requiring both-side approval and captured funds *before* a Commitment exists, and TTL-driven escalation to a collaboration queue. |
| 2 | [`02-layers-governance-security.md`](02-layers-governance-security.md) | The four-layer responsibility model — **protocol / operator / governance / security-and-fraud** — so it's unambiguous who owns ranking, trust, dispute resolution, Sybil resistance, and money. Answers "what are we doing with the governance layer, security, fraud prevention." |
| 3 | [`03-mvp-build-scope.md`](03-mvp-build-scope.md) | The **frozen v0 scope** — exactly what we build first, what we deliberately leave out, and the reference-build plan. This is the "decide what to build" artifact. |
| 4 | [`04-supply-demand-balance.md`](04-supply-demand-balance.md) | Undersupply vs. oversupply are opposite problems needing opposite fixes: undersupply is solved by pulling supply from a **federated** peer network; oversupply must **never** be solved by getting providers to coordinate and pressure demand (that's P1's cartel prohibition applied from a different trigger) — solved instead by governance-throttled supply growth and redirecting excess capacity to real demand elsewhere. |
| 5 | [`05-disputes-and-variable-duration.md`](05-disputes-and-variable-duration.md) | The **network-layer** (not policy) foundation for disputes: fulfillment as a variable-length window (a minute to multiple days) instead of a point in time, a dispute raisable by either party at any point in that window, an unconditional escrow freeze on dispute, category-defined checkpoints enabling partial settlement, and a closed vocabulary of terminal outcomes every operator's actual policy must resolve into. |

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
4. **A match is a staged proposal, not an instant commitment** (principle
   11). Both sides must explicitly approve and have funds captured
   (platform custody, not a third-party exchange) before a `Commitment`
   exists — forming a `Commitment` is already "agreement reached," never
   the final step. See `01` §P11.
5. **Escalation to collaboration is time-boxed, not immediate**
   (principle 12). An intent waits out its own timer in the demand queue
   before moving to a separate collaboration/negotiation queue — and
   pooled demand there can induce entirely new supply, not just match
   existing offers. See `01` §P12.
6. **Fulfillment is a window, and a dispute can happen mid-window**
   (principle 13). This is substantial enough to warrant its own file —
   see `05-disputes-and-variable-duration.md`.
