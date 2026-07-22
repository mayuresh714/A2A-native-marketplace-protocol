# Kernel schema (illustrative, not final)

Every core entity, expressed with exactly one extension point
(`category_ext`) where vertical-specific data lives. Compare against the
travel-specific schemas in `../design.md` §11 and each industry doc —
these are the same fields, generalized, with the vertical parts moved
into `category_ext` and validated separately against whatever schema the
relevant `ServiceCategory` registers (not shown here — that validation
schema is vertical-owned data, not part of the kernel).

```json
// ServiceCategory — registered once per vertical, never per transaction
{
  "type": "service_category",
  "category_id": "intercity_travel",
  "market_key_shape": ["corridor", "time_bucket"],
  "intent_ext_schema_ref": "schemas/intercity_travel/intent.json",
  "offer_ext_schema_ref": "schemas/intercity_travel/offer.json",
  "permitted_mechanisms": ["bilateral_bargaining", "sealed_bid_double_auction", "posted_price"],
  "required_attestations": ["vehicle_verification", "driver_identity"],
  "coalition_policy": {
    "enabled": true,
    "stance": "demand",
    "formation_mode": "ephemeral",
    "compatibility_check_ref": "schemas/intercity_travel/compatibility.json"
  },
  "default_autonomy_level": "auto_commit_within_scope",
  "fulfillment_evidence_schema_ref": "schemas/intercity_travel/evidence.json"
}

// Agent — identical shape regardless of category
{
  "type": "agent",
  "agent_id": "did:example:agent-789",
  "principal_ref": "principal-uuid",
  "profile_ref": "profile-uuid",
  "active_mandates": ["mandate-uuid-1"],
  "reputation_ref": "attestation-uuid"
}

// AgentProfile
{
  "type": "agent_profile",
  "profile_id": "profile-uuid",
  "service_categories": ["intercity_travel"],
  "stances": {"intercity_travel": ["supply"]},
  "negotiation_capabilities": ["bilateral_bargaining", "sealed_bid_double_auction"],
  "coalition_capable": {"intercity_travel": false},
  "attestation_refs": ["attestation-uuid-license", "attestation-uuid-insurance"]
}

// Intent — kernel fields identical across every vertical; category_ext varies
{
  "type": "intent",
  "intent_id": "uuid",
  "issuer_ref": "did:example:agent-123",
  "category_ref": "intercity_travel",
  "market_key": {"corridor": "Pune-Kolhapur", "time_bucket": "2026-07-18T15:00/17:00+05:30"},
  "constraints": {
    "time_window": {"earliest": "2026-07-18T14:30:00+05:30", "latest": "2026-07-18T17:00:00+05:30"},
    "budget_ceiling": {"amount": 400, "currency": "INR"},
    "quantity": 1
  },
  "category_ext": {
    "destination_waypoint": "Satara",
    "detour_tolerance_km": 10,
    "comfort_prefs": ["female_co_passengers_only"]
  },
  "coalition_opt_in": true,
  "mandate_ref": "mandate-uuid",
  "expiry": "2026-07-18T14:00:00+05:30"
}

// The same Intent kernel, a completely different category — note the
// kernel fields are byte-for-byte the same shape, only category_ext differs
{
  "type": "intent",
  "intent_id": "uuid",
  "issuer_ref": "did:example:agent-456",
  "category_ref": "home_healthcare",
  "market_key": {"skill": "post_surgical_wound_care", "geography": "geo-cell-88", "time_bucket": "2026-07-18T07:00/09:00+05:30"},
  "constraints": {
    "time_window": {"earliest": "2026-07-18T07:00:00+05:30", "latest": "2026-07-18T09:00:00+05:30"},
    "budget_ceiling": {"amount": 0, "currency": "INR", "note": "payer-set, not negotiated"},
    "quantity": 1
  },
  "category_ext": {
    "credential_required": "registered_nurse",
    "continuity_preferred": true,
    "scheme_ref": "insurance-scheme-uuid"
  },
  "coalition_opt_in": false,
  "mandate_ref": "mandate-uuid-2",
  "expiry": "2026-07-18T06:30:00+05:30"
}

// Offer
{
  "type": "offer",
  "offer_id": "uuid",
  "issuer_ref": "did:example:agent-789",
  "category_ref": "intercity_travel",
  "capacity": {"unit": "seat", "quantity": 3},
  "price_terms": {"negotiable": true, "current": {"amount": 550, "currency": "INR"}},
  "hold_expires_at": "2026-07-17T15:45:00+05:30",
  "category_ext": {
    "route": [
      {"stop": "Pune", "depart": "2026-07-18T15:30:00+05:30"},
      {"stop": "Satara", "eta": "2026-07-18T17:00:00+05:30"}
    ]
  },
  "attestation_refs": ["attestation-uuid-license"]
}

// Coalition — stance-tagged, otherwise identical whether demand- or supply-side
{
  "type": "coalition",
  "coalition_id": "uuid",
  "stance": "demand",
  "member_refs": ["intent-uuid-1", "intent-uuid-2", "intent-uuid-3"],
  "formation_mode": "ephemeral",
  "aggregation_rule_ref": "rules/interval_overlap_plus_additive_price.json",
  "compatibility_check_ref": "schemas/intercity_travel/compatibility.json",
  "status": "negotiating"
}

// Mandate
{
  "type": "mandate",
  "mandate_id": "uuid",
  "principal_ref": "principal-uuid",
  "holder_ref": "did:example:agent-123",
  "scope": {"category_ref": "intercity_travel", "budget_ceiling": {"amount": 3500, "currency": "INR"}},
  "autonomy_level": "auto_commit_within_scope"
}

// Commitment
{
  "type": "commitment",
  "commitment_id": "uuid",
  "negotiation_ref": "negotiation-uuid",
  "terms_snapshot": {"price": {"amount": 520, "currency": "INR"}, "time": "2026-07-18T15:45:00+05:30"},
  "status": "confirmed",
  "price_reference_check": {"within_band": true, "band": {"low": 480, "high": 560}},
  "mandate_ref": "mandate-uuid"
}

// Fulfillment
{
  "type": "fulfillment",
  "fulfillment_id": "uuid",
  "commitment_ref": "commitment-uuid",
  "outcome": "completed",
  "category_ext": {
    "evidence": {"drop_confirmed_at": "2026-07-18T17:02:00+05:30"}
  }
}

// Attestation
{
  "type": "attestation",
  "attestation_id": "uuid",
  "subject_ref": "did:example:agent-789",
  "claim_type": "vehicle_verification",
  "issuer": "attestation-service://regional-transport-registry",
  "expiry": "2027-01-01T00:00:00Z"
}
```

## Note on what's deliberately not shown here

`Market` and `ClearingMechanism` are runtime/registry-side objects (a
shard's live state and its currently-active mechanism), not
transaction-time messages the way the objects above are — they're covered
structurally in `02-generalized-flow.md` rather than given a wire schema
here, since their shape is closer to registry internal state than to a
message exchanged between agents.
