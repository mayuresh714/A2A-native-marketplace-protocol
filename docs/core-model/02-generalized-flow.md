# The generalized flow

One pipeline, expressed only in terms of the 14 entities from
`01-entities.md` — no vertical vocabulary. Every flow diagram in
`../design.md`, `../industries/`, and `../technical-deep-dive/` is this
pipeline with vertical-specific `category_ext` data plugged in.

## 1. The M×N arithmetic, generalized

The problem stated at the top of `../technical-deep-dive/01`: M
`supply`-stance agents and N `demand`-stance agents, naive matching
O(M×N). Nothing about that arithmetic is travel-specific — it's a
property of any two-sided population, so the fix generalizes exactly as
written, just with `market_key` replacing "corridor × time-bucket":

```
Market (market_key = category-defined dimensions)
  ├── active Intents  (N, demand-stance Agents)
  └── active Offers   (M, supply-stance Agents)
```

Sharding by `market_key` keeps each shard's population bounded regardless
of category — a home-healthcare shard keyed on (skill, geography,
time-bucket) has exactly the same tractability profile as a travel shard
keyed on (corridor, time-bucket); the dimensions differ, the sharding
logic doesn't.

## 2. The pipeline

```
                         ┌─────────────────────────────┐
                         │   ServiceCategory (registered) │
                         │   defines: market_key shape,    │
                         │   category_ext schema,          │
                         │   default ClearingMechanism,     │
                         │   required Attestation types,     │
                         │   Coalition applicability          │
                         └───────────────┬─────────────────┘
                                         │ governs
                                         ▼
Agent (demand stance) ──Intent──▶  Market shard  ◀──Offer── Agent (supply stance)
        │                              │                          │
        │ optional                    │ candidate                │ optional
        ▼                             │ generation                ▼
   Coalition (demand)                 │ + filtering          Coalition (supply)
        │                             ▼                          │
        └──────────────────▶  Negotiation  ◀────────────────────┘
                             (mechanism = shard's
                              ClearingMechanism:
                              posted-price | bilateral
                              bargaining | sealed-bid
                              auction | combinatorial
                              auction)
                                         │
                                         ▼
                                   Commitment
                        (checked against reference_band,
                         authorized by Mandate,
                         gated by autonomy_level —
                         auto_commit or require_confirmation)
                                         │
                                         ▼
                                   Fulfillment
                                         │
                                         ▼
                              Attestation update
                       (reputation feedback, both stances)
```

Every box in this diagram is one of the 14 entities. Nothing in the
diagram says "driver" or "diner" or "carrier" — those words only appear
inside a `ServiceCategory`'s `category_ext` schema, never in the pipeline
itself.

## 3. Stance symmetry, made explicit

Because `Coalition` and stance are both generalized (§ `01-entities.md`
7 and 1), the pipeline above is the *same* diagram whether:

- N `demand`-stance agents coalesce (travel/food consumer pooling,
  `../technical-deep-dive/02-consumer-collaboration-protocol.md`), or
- M `supply`-stance agents coalesce (event-vendor bundling, freight
  load-splitting, `../industries/event-services.md` §5-6), or
- neither side coalesces at all (the simple bilateral case every doc
  started from).

The protocol doesn't need three different flows for these — it needs one
flow plus a `stance` tag on the `Coalition`, which is the entire
generalization: earlier docs described "consumer coalitions" and "vendor
coalitions" as if they were different mechanisms; in the kernel they are
the same object with a different tag.

## 4. Provider isolation, generalized

`../technical-deep-dive/03-provider-isolation-and-discovery.md` described
isolation as a `supply`-stance-specific access-control rule. Generalized:
**within a `Market` shard, agents on the same stance are, by default,
isolated from seeing each other's live `Intent`/`Offer` content** — this
applies symmetrically to `demand`-stance agents too (two consumer agents
competing for the same scarce `supply`-stance capacity shouldn't see each
other's bids either, for the identical collusion-surface reason). The
access-control rule from `03-provider-isolation-and-discovery.md` §2
generalizes directly: two read paths, own-stance-facing (sees only
aggregate/anonymized signal) and cross-stance-facing (sees the specific
candidate offers relevant to your own `Intent`), with `Coalition`
formation as the sole, explicit, opt-in exception to same-stance
isolation.

## 5. Autonomy is a `ServiceCategory` default, not a protocol constant

`../design.md` and the industry docs disagreed on how much autonomy an
agent should default to (home-services allowed silent scope-expansion
auto-confirm within a mandate ceiling; home-healthcare required
human confirmation on every recurring visit even within an approved
mandate). Generalized: `autonomy_level` is a field on `Mandate`, with a
**default value supplied by the `ServiceCategory`**, not a single
protocol-wide constant — the kernel doesn't take a position on how much
autonomy is appropriate; each registered category does, and a principal
can always override a category's default toward *more* caution (never
toward less than the category's own floor, e.g. home-healthcare's
category definition should refuse to permit a `ServiceCategory` override
that allows silent recurring auto-commit).

## 6. Where mechanism choice comes from

A `Market` shard's `clearing_mechanism_ref` isn't fixed by the category
either — it's chosen dynamically based on the shard's actual liquidity at
matching time, using the same staging rule from
`../technical-deep-dive/04-price-discovery-mechanism-design.md` §2: thin
shards default to `bilateral_bargaining`, thick schedulable ones batch
into `sealed_bid_double_auction`, and any shard with active `Coalition`
participation requires `combinatorial_auction` for that negotiation
specifically. The `ServiceCategory` only supplies which mechanisms it
*permits* (a fixed-schedule category like rail only ever permits
`posted_price`) — the shard picks among the permitted set based on
real-time conditions.
