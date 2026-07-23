# Scaling to billions of agents: a go-to-market question, not just a compute one

`../technical-deep-dive/01-scale-and-matching-architecture.md` already
solved the compute side of scale — sharding by market key keeps matching
tractable regardless of how many agents exist globally, and marginal
compute cost per additional shard is close to zero. That is not the
binding constraint on reaching "billions of agents." **Liquidity and trust
don't shard the same way software does** — a new (corridor, time-bucket)
shard is computationally free to spin up, but it starts with zero
participants and zero reputation history regardless of how large the
global network gets elsewhere. This doc is the business sequencing that
actually gets from one working pilot to global scale, given that
constraint.

## 1. The core mistake to avoid: launching wide instead of deep

Because the technical architecture makes many simultaneous shards cheap,
the tempting move is to launch broadly — many verticals, many
geographies, at once — on the theory that scale itself will produce
liquidity. It won't: `../technical-deep-dive/06-caveats-and-practical-
realities.md` §1 already established that liquidity has a hard floor per
shard, and `../design.md` §13's own build order stages depth (bilateral →
multi-provider → coalitions → market-clearing) before breadth for exactly
this reason. The business version of that lesson: **prove one shard can
sustainably cross its liquidity threshold before opening a second one**,
rather than spreading thin across many that individually never cross it.

## 2. Staged rollout

**Phase 0 — one corridor, one vertical, one geography.**
A single intercity corridor (or a single city's home-services category)
with real, consenting providers. Goals: confirm the liquidity threshold is
reachable at all with real-world adoption friction (not just simulation),
and get a first real read on where actual operating cost lands relative to
the 2% target (`../technical-deep-dive/07` already expects this to run
materially higher than 2% at this stage — this phase is where that gets
measured, not assumed).

**Phase 1 — adjacent verticals, same geography.**
Expand to other high-fit verticals (`02-market-fit-framework.md`'s
high-scoring list) within the same city/region before expanding
geography. Rationale: attestation, compliance, and trust infrastructure
built for one vertical in a region (identity verification, dispute
handling processes, local payment-rail integration) is substantially
reusable across verticals in that same region, but not across regions —
this ordering captures the cheaper reuse first.

**Phase 2 — same verticals, new geography (same country).**
Only after Phase 1 verticals are working, replicate the same vertical set
into new cities/regions within one country — regulatory and payment-rail
patterns (`../technical-deep-dive/07` §3's UPI-style rail argument) are
consistent within a country, making this the next-cheapest expansion axis
before crossing a border.

**Phase 3 — the actual unlock: assistant-platform integration.**
This is where "billions of agents" becomes plausible rather than
aspirational. Direct, organic adoption by billions of individual
providers and consumers, one at a time, is not a realistic path — it has
to ride on the existing consumer distribution of general-purpose AI
assistants (`03-business-model-and-customers.md` §3's second customer
segment). This phase is explicitly gated on Phase 0-2 having produced
real, demonstrable liquidity and quality-of-match data — an assistant
platform has no reason to integrate against an unproven registry with
thin supply.

**Phase 4 — cross-border / multi-currency.**
Deliberately last. `../design.md` §14 and `../technical-deep-dive/06` §7-8
already flag cross-border regulatory and currency handling as unsolved
and out of scope for early phases — this phase only starts once
domestic regulatory and payment patterns are proven, not before.

## 3. What "billions of agents" actually looks like at the end state

Not one global market — **many thousands of independently-bootstrapped
shards**, each having individually crossed its own liquidity threshold,
stitched together by (a) a shared protocol/kernel
(`../core-model/`) so an agent built for one vertical/geography
interoperates with the infrastructure everywhere else, and (b) assistant-
platform integrations that give any individual consumer's agent a path
into whichever local shards are relevant to them. The billions-scale
number is a sum over many bounded, separately-won markets, not the result
of one network effect that propagates globally on its own — exactly the
same "no cross-shard consensus required" principle from
`../technical-deep-dive/01` §5, just true of adoption and trust instead of
compute.

## 4. The failure mode this roadmap is designed to prevent

Spreading effort across many unproven shards simultaneously, none of them
individually reaching the liquidity or trust density needed to be useful,
while claiming "billions of agents" as a roadmap slide rather than a
measured outcome. Every phase above is gated on the previous one
producing real evidence (liquidity crossed, cost ratio measured, dispute
rate acceptable) — not a calendar date — specifically to avoid that
failure mode.
