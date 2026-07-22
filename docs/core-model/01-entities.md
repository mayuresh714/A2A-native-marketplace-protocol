# Core entities

Fourteen entities. Every mechanism described in `../design.md`,
`../industries/`, and `../technical-deep-dive/` is an instance of one of
these — nothing vertical-specific appears in this list.

## 1. `Agent`

The single fundamental participant type. There is no `ConsumerAgent` /
`ProviderAgent` split — one `Agent` type, whose behavior in any given
interaction is determined by the **stance** it takes (§ below), not by
its identity.

| Field | Meaning |
|---|---|
| `agent_id` | Stable identifier (DID-style, per A2A's identity model) |
| `principal_ref` | The `Principal` this agent acts for |
| `profile_ref` | Its `AgentProfile` — what it's capable of negotiating |
| `active_mandates` | Currently valid `Mandate`s bounding its authority |
| `reputation_ref` | Its `Attestation`/reputation record |

An agent's **stance** in a given `Negotiation` is either `demand` (it's
seeking a service/capacity — the role travel called "consumer") or
`supply` (it's offering one — the role travel called "provider"). Stance
is a property of the negotiation, not the agent: nothing prevents one
agent from taking a `supply` stance in one `ServiceCategory` and a
`demand` stance in another, or even both within the same category (a
freight carrier's agent is `supply` when hauling a shipper's freight and
`demand` when it needs fuel or maintenance service — same `Agent` object,
declared via its `AgentProfile`, no special-casing required anywhere else
in the protocol).

## 2. `Principal`

The human or organization an `Agent` acts for. Kept distinct from `Agent`
because they aren't always the same set of people —
`../industries/home-healthcare.md` §3 already surfaced this: the person
who *authorizes* a booking, the person who *pays*, and the person who
*receives* the service can be three different humans.

| Field | Meaning |
|---|---|
| `principal_id` | Identifier for the human/org |
| `roles` | Subset of `{authorizer, payer, beneficiary}` this principal holds for a given `Mandate`/`Commitment` |

A simple consumer booking a solo trip collapses all three roles into one
principal — the general case doesn't require that collapse, and the
schema shouldn't assume it.

## 3. `AgentProfile`

The capability declaration — a generalization of A2A's "agent card" plus
what travel's provider/consumer schemas each declared implicitly.
Declares, for a given `Agent`:

| Field | Meaning |
|---|---|
| `service_categories` | Which `ServiceCategory` entries this agent can transact in |
| `stances` | Which stance(s) — `demand`, `supply`, or both — it's willing to take, per category |
| `negotiation_capabilities` | Which `ClearingMechanism` types it can participate in (fixed quote-only, bilateral bargaining, sealed-bid auction, combinatorial auction — `../technical-deep-dive/04-price-discovery-mechanism-design.md`) |
| `coalition_capable` | Whether this agent can participate in `Coalition` formation, and on which stance |
| `attestation_refs` | Verifiable claims backing its capability declarations (license, insurance, etc.) |

This is the object that makes an agent's behavior legible to the rest of
the market *before* any negotiation starts — a market shard can filter
candidates by profile without needing to understand the vertical at all.

## 4. `Intent`

A generalized "I want X," issued by an `Agent` taking the `demand` stance.
Replaces `TripIntent` and every vertical-specific intent object in
`../industries/`.

| Field | Meaning |
|---|---|
| `intent_id` | Identifier |
| `issuer_ref` | The `Agent` (in `demand` stance) |
| `category_ref` | Which `ServiceCategory` this intent belongs to |
| `market_key` | The dimensions used for shard placement (`../technical-deep-dive/01`) — category-defined, not hardcoded (e.g. corridor+time for travel, skill+geography+time for home-healthcare) |
| `constraints` | Core constraints common to all categories: time window, budget ceiling, quantity |
| `category_ext` | Category-specific fields (route waypoints, dietary flags, urgency tier, credential requirements — never in the core schema, see `04-schema.md`) |
| `coalition_opt_in` | Whether this intent may join a `Coalition` |
| `mandate_ref` | The `Mandate` authorizing this agent to act on it |
| `expiry` | When this intent lapses if unmatched |

## 5. `Offer`

A generalized response to (or proactive posting against) an `Intent`,
issued by an `Agent` in `supply` stance. Replaces travel's `Offer`,
home-services' quote, freight's load-capacity posting, etc.

| Field | Meaning |
|---|---|
| `offer_id` | Identifier |
| `issuer_ref` | The `Agent` (in `supply` stance) |
| `category_ref` | `ServiceCategory` |
| `capacity` | Generic unit of what's being offered (seats, a table-time-slot, a job-slot, freight weight/volume) |
| `price_terms` | Fixed or negotiable, and the current price/range |
| `hold_expires_at` | Perishability boundary (`../technical-deep-dive/01` §3) |
| `category_ext` | Category-specific fields |
| `attestation_refs` | Trust signals backing this specific offer |

## 6. `Negotiation`

The generalized exchange between one or more `demand`-stance and one or
more `supply`-stance agents (or `Coalition`s standing in for a group of
either). Replaces the travel-specific offer/counter/accept flow in
`../design.md` §10, and generalizes it to whichever `ClearingMechanism`
actually governs this category/shard.

| Field | Meaning |
|---|---|
| `negotiation_id` | Identifier |
| `participants` | `Agent`/`Coalition` refs on each side |
| `mechanism_ref` | Which `ClearingMechanism` governs this negotiation |
| `round_count` / `max_rounds` | Bound on back-and-forth (`../technical-deep-dive/04`) |
| `status` | `open \| converged \| failed \| expired` |

## 7. `Coalition`

A generalized, ephemeral-by-default grouping of same-stance `Agent`s that
negotiate jointly. Symmetric by construction — a `Coalition` can form on
the `demand` side (travel/food consumer pooling) or the `supply` side
(event-vendor bundling, freight two-truck load-splitting) using the exact
same object, just tagged with which stance formed it.

| Field | Meaning |
|---|---|
| `coalition_id` | Identifier |
| `stance` | `demand` or `supply` |
| `member_refs` | Member `Agent`s |
| `formation_mode` | `ephemeral` (dissolves after one negotiation, the default) or `standing` (persists across negotiations, must be disclosed per `../industries/event-services.md` §8) |
| `aggregation_rule_ref` | How member constraints combine into one joint `Intent`/`Offer` (time-window intersection, price-sum or proportional split — `../technical-deep-dive/02` §4) |
| `compatibility_check_ref` | Category-defined compatibility rule members must clear (comfort preferences for travel, cargo-class compatibility for freight — never a core-schema field, since what "compatible" means is category-specific) |
| `status` | `forming \| negotiating \| proposed \| accepted \| rejected \| expired \| dissolved` |

## 8. `Mandate`

The human-to-agent authorization boundary, adopted directly from AP2's
Intent/Cart Mandate model and generalized across every vertical.

| Field | Meaning |
|---|---|
| `mandate_id` | Identifier |
| `principal_ref` | The authorizing `Principal` |
| `holder_ref` | The `Agent` it authorizes |
| `scope` | Budget ceiling, category restriction, time bound |
| `autonomy_level` | `auto_commit_within_scope` or `require_confirmation` — the default varies by category (home-healthcare defaults to `require_confirmation` even within scope, per `../industries/home-healthcare.md` §5; a routine home-services repair can default to `auto_commit_within_scope`) |

## 9. `Commitment`

The binding state once a `Negotiation` (solo or via `Coalition`) converges.

| Field | Meaning |
|---|---|
| `commitment_id` | Identifier |
| `negotiation_ref` | What converged into this |
| `terms_snapshot` | Final agreed terms, immutable once recorded |
| `status` | `held \| confirmed \| expired \| reneged` |
| `price_reference_check` | Whether the price cleared within the published reference band (`../technical-deep-dive/04` §3) |
| `mandate_ref` | The `Mandate` this commitment was authorized under |

## 10. `Fulfillment`

The execution-and-confirmation record — what actually happened, checked
against `Commitment`.

| Field | Meaning |
|---|---|
| `fulfillment_id` | Identifier |
| `commitment_ref` | What this fulfills |
| `evidence` | Category-defined evidence (delivery confirmation, signed job completion, GPS/telemetry — via `category_ext`, same extension pattern as `Intent`/`Offer`) |
| `outcome` | `completed \| partial \| failed \| disputed` |

## 11. `Attestation`

A verifiable claim about an `Agent` or `Principal` — license, insurance,
background check, or accumulated reputation score. One entity kernel,
category-specific claim types (a plumbing license and a nursing
registration are both `Attestation`s, differently typed via
`category_ext`, never different core entities).

| Field | Meaning |
|---|---|
| `attestation_id` | Identifier |
| `subject_ref` | `Agent` or `Principal` this is about |
| `claim_type` | Category-defined (license, insurance, past-rating-aggregate, verified-identity) |
| `issuer` | Who verified this (a registry-affiliated attestation service, a licensing board integration, aggregated consumer feedback) |
| `expiry` | Attestations can lapse and need re-verification (relevant especially where `../industries/home-healthcare.md` requires periodic re-check, not one-time) |

## 12. `Market` (shard)

The matching context — generalizes `../technical-deep-dive/01`'s
(corridor, time-bucket) shard to an arbitrary, category-defined key.

| Field | Meaning |
|---|---|
| `market_key` | Category-defined dimensions (travel: corridor × time-bucket; home-healthcare: skill × geography × time-bucket; freight: lane × time-bucket) |
| `category_ref` | `ServiceCategory` |
| `active_intents` / `active_offers` | Current population in this shard |
| `clearing_mechanism_ref` | Which `ClearingMechanism` this shard currently runs (can change as liquidity changes — thin markets default to bilateral bargaining, thick ones batch into a sealed-bid auction, per `../technical-deep-dive/04` §2) |
| `reference_band` | Current published price reference (`../technical-deep-dive/04` §3) |

## 13. `ClearingMechanism`

The pluggable pricing/matching algorithm attached to a `Market` shard —
one of the four evaluated in `../technical-deep-dive/04-price-discovery-
mechanism-design.md`: `posted_price` (quote-only, no negotiation — fixed-
schedule providers), `bilateral_bargaining`, `sealed_bid_double_auction`,
`combinatorial_auction` (required whenever `Coalition`s or bundled offers
are involved). Which one governs a given `Market` is a property of that
shard's liquidity and whether bundling applies — not a fixed protocol
choice.

## 14. `ServiceCategory`

The extensibility backbone — see `03-extensibility-and-vertical-
mapping.md` for full treatment. A registered definition of:

- what `category_ext` schema `Intent` and `Offer` must validate against
  for this category,
- the default `ClearingMechanism` and `autonomy_level`,
- what `Attestation` claim types are required before an agent's offers are
  even shown,
- whether `Coalition` formation is applicable, and on which stance,
- the `compatibility_check` rule a `Coalition` in this category must
  apply (if any).

Adding intercity travel, home services, food, freight, home healthcare, or
event services to this protocol is registering one `ServiceCategory` each
— never a change to entities 1-13.
