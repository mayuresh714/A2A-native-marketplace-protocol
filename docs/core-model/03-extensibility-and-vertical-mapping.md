# Extensibility: `ServiceCategory` as the only plug-in point

## 1. The rule

**Adding a vertical means registering one `ServiceCategory` object. It
never means adding a field to `Agent`, `Intent`, `Offer`, `Negotiation`,
`Coalition`, `Mandate`, `Commitment`, `Fulfillment`, `Attestation`, or
`Market`.** Every vertical-specific detail — route waypoints, dietary
flags, urgency tiers, cargo compatibility, medical credentials, vendor
bundling rules — lives inside the `category_ext` block of `Intent`/
`Offer`/`Fulfillment`/`Attestation`, validated against a schema the
`ServiceCategory` itself supplies. If a new vertical seems to need a new
*core* field, that's a signal the kernel is under-generalized, not a
reason to special-case the vertical — check `01-entities.md` again before
extending the kernel.

A `ServiceCategory` registration supplies:

| Declares | Example |
|---|---|
| `market_key_shape` | Which dimensions define a `Market` shard for this category |
| `intent_ext_schema` / `offer_ext_schema` | The category-specific fields `Intent`/`Offer` must carry |
| `permitted_mechanisms` | Which `ClearingMechanism` types are allowed (a fixed-schedule category permits only `posted_price`) |
| `required_attestations` | What `Attestation` claim types gate whether an offer is even shown |
| `coalition_policy` | Whether `Coalition` formation applies, on which stance, and the `compatibility_check` rule if any |
| `default_autonomy_level` | The `Mandate.autonomy_level` a principal starts from for this category (§`02-generalized-flow.md` §5) |
| `fulfillment_evidence_schema` | What `Fulfillment.evidence` must contain |

## 2. Proof: mapping all six verticals covered so far onto the kernel

| Vertical | `market_key_shape` | `intent_ext_schema` highlights | `permitted_mechanisms` | `coalition_policy` | `default_autonomy_level` |
|---|---|---|---|---|---|
| Intercity travel (`../design.md`) | corridor × time-bucket | route waypoints, seats, detour tolerance, comfort prefs | bilateral bargaining (thin), sealed-bid auction (thick), posted-price (rail/bus) | demand-side, ephemeral, compatibility check = comfort prefs | `require_confirmation` for coalition commits, `auto_commit_within_scope` for solo bilateral |
| Home services (`../industries/home-services.md`) | skill × geography × urgency-tier | job description/photos, urgency tier, scope-expansion ceiling | bilateral bargaining; posted-price for emergency tier | supply-side route-batching only (not consumer-facing) | `auto_commit_within_scope` (scope changes within pre-authorized ceiling) |
| Food & dining (`../industries/food-and-dining.md`) | venue/kitchen × time-slot | party size, dietary constraints, delivery zone | bilateral bargaining (table booking), posted-price (menu ordering) | demand-side, ephemeral, compatibility check = none (members never meet) | `auto_commit_within_scope` |
| Freight & logistics (`../industries/freight-logistics.md`) | lane × time-bucket | equipment type, weight/volume, cargo class | sealed-bid double auction (recommended from day one, `../technical-deep-dive/04` §2), combinatorial auction for backhaul bundling | both stances (shipper-side load bundling, carrier-side capacity-splitting), standing coalitions allowed if disclosed | `require_confirmation` (B2B, high value) |
| Home healthcare (`../industries/home-healthcare.md`) | skill × geography × time-bucket | credential requirements, continuity constraint, scheme/payer reference | posted-price (payer-set rates) predominant | none (explicitly disabled at the category level, `../industries/home-healthcare.md` §6) | `require_confirmation`, and the category **refuses** any override toward `auto_commit` even within an approved mandate |
| Event services (`../industries/event-services.md`) | vendor-category × date-window × geography | guest count, budget allocation across vendor categories, bundle composition | combinatorial auction (bundling is the default case, not the exception) | supply-side, standing coalitions expected and must be disclosed | `require_confirmation` |

Every row is *data* — none of it required touching `01-entities.md`. That
this table can be filled in for six structurally different markets
(urgent vs. scheduled, B2C vs. B2B, negotiable vs. payer-fixed price,
demand-side vs. supply-side pooling, coalition-forbidden vs.
coalition-default) without a single kernel change is the actual argument
that the generalization holds, not just an assertion that it should.

## 3. What breaks the abstraction (and the fix, if it ever happens)

Two honest failure modes to watch for as new verticals get added:

- **A field that seems to need to be core but is claimed to be
  category-specific for convenience.** Example risk: `price_terms` on
  `Offer` currently assumes a single scalar/range — a vertical with
  genuinely multi-dimensional pricing (e.g., dynamic bundling with
  per-component pricing that doesn't reduce to one number until a
  `Coalition` resolves it) might need `price_terms` itself restructured at
  the kernel level, not just extended. If a second vertical independently
  needs the same kernel change, that's real signal to revise
  `01-entities.md` — a single occurrence should stay in `category_ext`
  first.
- **A `ServiceCategory` whose `coalition_policy` or `default_autonomy_level`
  quietly gets weakened under business pressure** (e.g., a category
  originally set to `require_confirmation` getting relaxed to
  `auto_commit` to reduce friction) — the kernel's generalization doesn't
  protect against this; it's a governance question for whoever operates
  the `ServiceCategory` registry (`../technical-deep-dive/05-moat-and-
  strategy.md`'s neutral-operator role), not something `01-entities.md`
  can enforce by itself. Categories touching health, safety, or high
  financial exposure should have their `default_autonomy_level` floor
  locked against downward revision, analogous to home-healthcare's
  explicit refusal in the table above.
