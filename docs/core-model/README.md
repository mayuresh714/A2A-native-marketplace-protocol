# Core model: a generalized protocol, not a travel protocol with plug-ins

Everything so far has been built vertical-first: `../design.md` defined
`TripIntent`/`Offer`/`Commitment` for travel, then `../industries/` showed
five more verticals each with their own intent/offer shape, then
`../technical-deep-dive/` worked out matching, collaboration, and pricing
mechanics — mostly still described in travel's vocabulary even when the
ideas were already general (route decomposition, comfort-compatibility,
coalition formation).

That's backwards for a protocol meant to generalize. This folder inverts
it: define one small **kernel** of entities that has no vertical baked
into it at all, plus exactly **one formal extension point**, and treat
every vertical seen so far — travel included — as *data registered against
that kernel*, not a special case the protocol needs to know about.

## The one-sentence idea

**There is one entity, Agent — not a ConsumerAgent type and a
ProviderAgent type.** "Consumer" and "provider" are not kinds of agent;
they're a *stance* — demand-stance or supply-stance — that an Agent takes
within one specific negotiation, declared by its `AgentProfile` and
bounded by its current `Mandate`. Nothing else in this design requires two
separate object hierarchies for the two sides of a market. This single
choice is what makes the rest of the generalization fall out cleanly: the
same kernel that matched a rider to a driver in `../design.md` is, without
modification, the kernel that matches a shipper to a carrier
(`../industries/freight-logistics.md`) or a diner to a restaurant
(`../industries/food-and-dining.md`) — those docs just look like different
data plugged into the same entities, once you stop hard-coding "route" and
"seats" into the core schema.

## Files in this folder

| File | Content |
|---|---|
| [`01-entities.md`](01-entities.md) | The full entity list — `Agent`, `Principal`, `AgentProfile`, `Intent`, `Offer`, `Negotiation`, `Coalition`, `Mandate`, `Commitment`, `Fulfillment`, `Attestation`, `Market`, `ClearingMechanism`, `ServiceCategory` — what each one is, its fields, and which earlier vertical-specific object it replaces. |
| [`02-generalized-flow.md`](02-generalized-flow.md) | The single M×N matching/negotiation/collaboration/settlement pipeline, written with no vertical assumptions — the generalized version of the travel-specific flows in `../design.md` and `../technical-deep-dive/01-scale-and-matching-architecture.md`. |
| [`03-extensibility-and-vertical-mapping.md`](03-extensibility-and-vertical-mapping.md) | The `ServiceCategory` plug-in mechanism — how a new vertical is added as *registered data*, never a protocol change — proven concretely by mapping all six verticals covered so far onto the kernel. |
| [`04-schema.md`](04-schema.md) | Concrete schema definitions for the kernel entities, each with a single open `category_ext` extension block validated against its `ServiceCategory`'s own schema. |

## Why this matters beyond tidiness

A protocol that's secretly travel-shaped fails the moment a genuinely
different vertical needs a field the schema didn't anticipate (this
already happened once — `route` as a single origin-destination pair had
to be redone as a waypoint list to fit pooling, and comfort-preferences
had to be bolted on for coalition formation). A kernel with one real
extension point instead of ad hoc schema growth means adding vertical
#7 is a data-registration exercise, not a spec revision — which is also
the only way an *open* protocol (`../technical-deep-dive/05-moat-and-
strategy.md`) stays open: implementers extend it without forking it.
