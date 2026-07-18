# Consumer-agent collaboration protocol

Short answer to "can consumer agents collaborate with each other to make
counter-offers": yes, and it's not a minor feature — it's the mechanism
(main design doc §5) that turns several individually-unviable requests
into one viable one. This doc works out the mechanics precisely, since
"agents collaborate" is easy to say and easy to under-specify.

## 1. Who finds whom

Consumer agents don't discover each other directly (no global chatter
between arbitrary strangers' agents) — discovery is mediated through the
same sharded registry as provider matching (`01-scale-and-matching-
architecture.md`). An intent opts in to coalition-discovery by setting
`coalition_opt_in: true`; only opted-in intents in the same (corridor,
time-bucket) shard become visible to each other as coalition candidates.
No opt-in, no exposure — this is the default-isolation principle from
`03-provider-isolation-and-discovery.md` applied to consumers instead of
providers.

## 2. Coordinator problem: don't require true peer consensus

A naive design has N consumer agents negotiating with each other as true
peers, reaching agreement via some kind of distributed consensus. This is
unnecessary complexity for a problem that doesn't need Byzantine-level
guarantees — these agents don't need to *trust* each other, they need to
converge on one joint proposal or fail fast. Two designs:

- **(a) Full peer-to-peer** — every candidate talks to every other
  candidate directly, converges via gossip/voting. Correct in principle,
  slow, and adds real distributed-systems complexity (partial failures,
  message ordering) for a case where the group size is small (2-5
  members, typically) and doesn't need to survive network partitions.
- **(b) Registry-hosted ephemeral coalition session** — the registry shard
  hosts a short-lived, disposable session object; candidate agents connect
  to it, and it relays proposals between them (does not itself decide
  anything). This keeps the actual negotiation logic fully in the
  agents — the registry is a dumb relay, not a decision-maker — while
  avoiding peer-to-peer consensus machinery for a small, short-lived group.

**(b) is the recommended default.** It's not a central authority making
matching decisions (that stays in the anti-cartel-sensitive territory
`04-price-discovery-mechanism-design.md` is careful about); it's
infrastructure-level message relay, no different in kind from the registry
already relaying consumer↔provider messages.

## 3. Coalition lifecycle (state machine)

```
FORMING → NEGOTIATING → PROPOSED → { ACCEPTED | REJECTED | EXPIRED } → DISSOLVED
```

- **FORMING** — one agent's intent enters a shard's coalition-discovery
  pool; the registry surfaces other opted-in, plausibly-compatible
  intents (overlapping time windows, same corridor, passing the
  compatibility check from §4).
- **NEGOTIATING** — candidate agents exchange proposals through the
  session (departure time, drop points, price split — see §4 for the
  actual aggregation math) for a bounded number of rounds.
- **PROPOSED** — the group converges on one joint offer and sends it to a
  provider agent as a single `CoalitionOffer`.
- **ACCEPTED / REJECTED / EXPIRED** — provider's response, or a timeout.
- **DISSOLVED** — always terminal, whether the coalition booked
  successfully or fell apart. No coalition persists as a standing entity
  by default (contrast: `../industries/event-services.md`'s vendor
  coalitions are the deliberate exception — opt-in, standing, disclosed).

Every state transition needs a bound: max negotiation rounds, and an
overall wall-clock timeout after which an agent abandons the coalition
attempt and falls back to its own best solo offer, rather than blocking
indefinitely on group convergence (`../design.md` §12 flags this
explicitly — coalition formation must not out-stall the underlying
capacity's own hold expiry).

## 4. The actual aggregation math

A joint counter-offer needs concrete rules for turning N individual
intents into one proposal, not just "they negotiate and agree":

- **Time convergence.** Each member has an acceptable window
  `[earliest_i, latest_i]`. The candidate departure time is chosen to
  maximize the number of members whose window contains it — i.e. find the
  point of maximum overlap across the set of intervals (a standard
  interval-scheduling computation, not a negotiation at all — this part
  should be computed, not haggled over). If no single point clears every
  member's window, the coalition either drops the least-flexible member
  (with that member's agent's consent) or fails and each falls back to
  solo offers.
- **Price aggregation.** Two structurally different cases:
  - *Additive* (each member pays for their own segment, e.g. the
    Pune-Satara/Vadgaon/Ichalkaranji example — the joint offer's total
    price is just the sum of each member's own segment price, no real
    negotiation needed between members on this axis).
  - *Shared-cost split* (e.g. a whole-vehicle charter split among a group
    with no natural per-person segmentation) — needs an actual bargaining
    rule; a defensible default is proportional-to-individual-ceiling
    splitting (each member's share of the total is proportional to what
    they individually declared as their ceiling), which is simple, hard
    to game asymmetrically, and doesn't require members to see each
    other's exact ceilings (only their own share, computed by the
    session, needs to be revealed to them).
- **Unanimous consent to commit, always.** Regardless of how the joint
  proposal was computed, `../design.md` §6 already requires a human
  confirmation checkpoint before finalizing any stranger coalition — that
  applies here without exception: coalition negotiation produces a
  *proposal*, never a binding commitment, until every member's human has
  confirmed. One member declining at that final step should gracefully
  degrade the coalition (drop that member, re-check if the remaining
  group's joint offer is still viable) rather than failing the whole
  thing outright when avoidable.

## 5. Adversarial members

Coalition members are mutual strangers, acting through agents, with no
prior trust relationship — unlike a consumer agent negotiating with a
known-reputable provider, a coalition partner could act in bad faith:

- **Stalling** — an agent that keeps countering without converging to run
  out another member's patience or the capacity's hold expiry. Mitigated
  by the bounded-rounds/timeout rule in §3 — stalling just causes that
  member to be dropped or the whole coalition to expire, not to be
  rewarded.
- **Bad-faith proposals designed to extract concessions** (e.g.,
  repeatedly proposing timings it knows another member can't accept, to
  pressure a better price split). Mitigated by reputation: an agent whose
  principal has a track record of causing coalition failures after
  joining should be deprioritized as a coalition candidate in future
  matching, the same way a provider with poor fulfillment history is
  deprioritized.
- **Compatibility misrepresentation** (claiming to pass a comfort check it
  doesn't actually meet, to force inclusion) — see
  `../design.md` §6 and §12; this needs both a technical check (where a
  constraint can be verified, e.g., a genuinely verified attestation
  rather than a self-declared field) and a reputational consequence for
  agents whose principals are later reported as having misrepresented
  themselves.
