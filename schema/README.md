# v0 wire schemas

The **frozen v0 wire contract** — the typed messages and records agents
speak on this protocol. This is the first code artifact of the project;
everything else (the simulator, the reference implementation) is written
against these. Scope and rationale: [`../docs/spec/03-mvp-build-scope.md`](../docs/spec/03-mvp-build-scope.md).

- **Format:** JSON Schema draft 2020-12.
- **Version:** `0.1.0` (the `protocol_version` const in the envelope).
- **Vertical:** intercity ride-pooling (the v0 reference category).
- **Money:** always integer minor units + ISO-4217 currency — never floats.
- **IDs:** agents/principals are DIDs; records use UUIDs.

## Layout

```
schema/
  common.schema.json              shared $defs (did, uuid, money, region, timeWindow, signature, ...)
  core/                           the entity/record types
    agent.schema.json             one participant type; stance is per-negotiation
    mandate.schema.json           human→agent authorization boundary (AP2-derived)
    intent.schema.json            demand request — three-tier: grouping_keys / constraints / preferences
    offer.schema.json             supply posting — route as waypoints in category_ext
    coalition.schema.json         demand-ONLY pooling (stance is a const, not enum)
    match-proposal.schema.json    a STAGED match, not yet binding — awaits dual approval + funds
    commitment.schema.json        the AGREEMENT (not final) once both sides approve + escrow held
    fulfillment.schema.json       the three release gates: consumer + provider + platform
    dispute.schema.json           raisable mid-window; unconditional freeze; closed outcome set
    settlement.schema.json        terminal money movement, thin fee
    attestation.schema.json       signed claims; ratings must reference a settled commitment
  messages/                       wire traffic
    envelope.schema.json          typed envelope — NO free-text channel (injection defense)
    counter-offer.schema.json     bilateral negotiation move
    decision.schema.json          accept / decline (coded reasons only)
    coalition-proposal.schema.json   demand↔demand pooling proposal
    coalition-offer.schema.json      the joint offer to a provider
  categories/intercity-travel/    the v0 category package (pluggable per docs/core-model/03)
    grouping-keys.schema.json     source_region + destination_region + start_time_bucket
    intent-ext.schema.json        soft preferences (comfort, detour, min rating)
    offer-ext.schema.json         ordered route waypoints, vehicle
    evidence.schema.json          dropoff/GPS trace for platform verification
  examples/                       valid instances of the Pune–Kolhapur scenario
```

## How the schemas encode the principles

| Principle (see `../docs/spec/01`) | Where it lives in the schema |
|---|---|
| P1 — consumers pool, providers don't | `coalition.schema.json`: `stance` is `{"const": "demand"}` — a supply coalition fails validation |
| P3 — grouping keys ≠ constraints ≠ preferences | `intent.schema.json`: three separate blocks, with grouping keys constrained to the coarse category schema |
| P4 — fraud prevention | `envelope` has no free-text (injection); `attestation` ratings require a settled commitment |
| P5 — collaborate on failure | `coalition-proposal` / `coalition-offer` messages, triggered only after solo match fails |
| P6 — FIFO within partition | `intent.created_at` / `offer.created_at` are the ordering key; `counter_offer.round` bounds negotiation |
| P7 — transaction on match | a `match_proposal` reaching `status: approved` → `commitment` |
| P8 — money only on dual approval + evidence | `commitment.escrow.state` + `fulfillment`'s three gates + `settlement` |
| P10 — ranking is the operator's | absent by design — no ranking/score field is in the protocol; it's operator policy |
| P11 — staged proposal, dual approval, platform-custody escrow | `match-proposal.schema.json`'s `consumer_approved`/`provider_approved` gate before any `commitment.schema.json` exists; `commitment.status: confirmed` explicitly means "agreement, not final" |
| P12 — time-boxed escalation to collaboration | `intent.schema.json`'s `solo_wait_seconds` gates when a coalition attempt is even eligible |
| P13 — variable duration + mid-window disputes | `commitment.schema.json`'s `fulfillment_window`; `dispute.schema.json`'s unconditional freeze and closed `outcome` vocabulary (see `../docs/spec/05`) |

## Validation

Any JSON Schema 2020-12 validator works. Example with `ajv` (once tooling
is added):

```
ajv validate -s schema/core/intent.schema.json \
  -r "schema/common.schema.json" \
  -d schema/examples/intent.pune-satara.json
```

Category-extension validation (validating `intent.preferences` against
`categories/intercity-travel/intent-ext.schema.json`, and
`intent.grouping_keys` against that category's `grouping-keys.schema.json`)
is performed by the runtime using the `category_ref`, since JSON Schema
alone doesn't dispatch on a sibling field's value. That dispatch logic is
part of the reference implementation (the next build step), not the static
schemas.

## Status

Frozen for v0. Changes go through a version bump (`0.1.0` → `0.2.0`) with
capability negotiation, per `../docs/platform-architecture/01` §2 — not by
mutating these files silently.
