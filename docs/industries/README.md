# Industry applications

The core protocol (`../design.md`) is not travel-specific — the underlying
pattern is: **perishable capacity or availability, held by many
independent, mutually-unknown providers, needed by many consumers, where
today a human on at least one side manually searches/waits/haggles.**
Intercity ride-sharing was the motivating example; this folder works
through five other industries where the same pattern applies, to test
whether the protocol generalizes or was accidentally travel-shaped.

Each doc follows the same structure so they're comparable:

1. Why this industry fits the pattern
2. Today's pain, both sides
3. Actors / provider types
4. Market structure (on-demand vs. scheduled, negotiable vs. fixed price,
   perishable-time vs. perishable-stock)
5. A worked example (concrete numbers, mirrors the Pune–Kolhapur walkthrough
   in the main design doc)
6. Coalition/pooling angle, if one exists for this vertical — and on which
   side (consumer, provider, or both)
7. Price-discovery / anti-cartel considerations specific to the vertical
8. Trust, safety, and compliance caveats specific to the vertical
9. Why this could be high-impact

## The five picked, and why these five

Chosen to stress-test different facets of the protocol, not to all look
like the same example restated:

| Industry | Doc | What it stresses that travel didn't |
|---|---|---|
| **Home services** (electrician, plumber, handyman) | [`home-services.md`](home-services.md) | Urgent on-demand *and* scheduled in the same market; price isn't knowable until the job is inspected (variable materials/scope); in-home physical safety trust is the dominant constraint. |
| **Food & dining** (restaurant table booking, food ordering) | [`food-and-dining.md`](food-and-dining.md) | Perishable capacity is a *time-slot* (a table, a kitchen ticket slot) not a vehicle seat; group-order and delivery-batching pooling is consumer-side and provider-side at once. |
| **Freight & logistics** (trucking backhaul matching) | [`freight-logistics.md`](freight-logistics.md) | Pure B2B, high-value, and the "empty return leg" problem *is* the demand-aggregation problem from the main doc, already attempted centrally (Uber Freight, Convoy) — good test of whether decentralizing it changes the outcome. |
| **Home healthcare** (non-emergency nursing/physio/elder care visits) | [`home-healthcare.md`](home-healthcare.md) | Forces the protocol to be conservative: heavy credentialing, regulatory compliance, and far less auto-commit than any other vertical here — a useful lower bound on how much autonomy the protocol should ever grant by default. |
| **Event services** (wedding/event vendor bundling — caterer, photographer, decorator, venue) | [`event-services.md`](event-services.md) | Coalition formation on the *supply* side — several different provider types bundling into one package for one consumer — the mirror image of the consumer-side coalition in the main design doc. |

## What's common across all five (so it's not re-derived per doc)

- Same base layering: A2A (discovery/transport) → AP2 (payment mandates) →
  this protocol's negotiation/marketplace layer (see `../design.md` §9).
- Same core objects: `Intent`, `Offer`, `Counter`, `Commitment`,
  `Fulfillment`, reputation feedback — field contents differ per vertical,
  message *shape* doesn't.
- Same non-negotiables carried over from the main doc: human-authorized
  mandates bound agent spend/scope (never silent unbounded commitment);
  hold-with-expiry semantics for anything perishable; reputation/attestation
  as a first-class object, not a platform afterthought.
- Same open risk to design against in every vertical, not just travel:
  independent provider agents converging on inflated pricing. Each doc
  below notes what "cartel-like" looks like in that specific market and
  whether the main doc's market-clearing approach (§7) transfers as-is or
  needs adjustment.
