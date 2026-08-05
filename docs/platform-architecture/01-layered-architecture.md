# Layered architecture: what's core, what's a plugin, what's the deployer's

"Anyone can leverage it, plug-and-play, self-host on their own infra" is a
precise architectural requirement, not a marketing line. It only holds if
you draw hard boundaries between what the protocol *fixes* and what a
deployer is free to *swap*. Get the boundary wrong in either direction and
the promise breaks: too much in the fixed core and deployers can't use
their own infra; too little and independent deployments stop
interoperating (the classic fragmentation failure of under-specified open
standards).

## 1. The three layers

```
┌───────────────────────────────────────────────────────────────┐
│  LAYER 3 — DEPLOYER-OWNED (ops)                                 │
│  their cloud, their clusters, their scaling, their SLAs,        │
│  their category schemas, their business policy                  │
├───────────────────────────────────────────────────────────────┤
│  LAYER 2 — ADAPTERS (pluggable "drivers")                       │
│  storage · payment rail · identity/attestation · clearing       │
│  mechanism · transport · category-schema packages               │
│  (well-defined interfaces in core; implementations swappable)   │
├───────────────────────────────────────────────────────────────┤
│  LAYER 1 — CORE (stable, versioned, open spec)                  │
│  entity model · wire message formats · negotiation state        │
│  machine · mandate/authorization semantics · identity model ·   │
│  the ServiceCategory extension interface · conformance rules    │
└───────────────────────────────────────────────────────────────┘
```

This is **hexagonal / ports-and-adapters architecture** applied to a
protocol: Layer 1 defines the *ports* (interfaces + wire contract), Layer
2 is the *adapters* implementing those ports, Layer 3 is where a deployer
runs the assembled thing. The direct precedents are Kubernetes (a stable
core API + CSI/CNI/CRI interfaces the ecosystem writes drivers against)
and Terraform (a core + a provider-plugin interface). You self-host
Kubernetes on any cloud precisely because the storage/network/runtime
concerns are behind swappable interfaces — the same trick is what lets a
deployer here run on their own infra.

## 2. Layer 1 — the stable core (what MUST be identical everywhere)

This is the part that can never be deployer-specific, because it's exactly
what lets two independently-built deployments understand each other. It's
deliberately small — the smaller the fixed core, the easier adoption and
the lower the fragmentation risk.

- **Entity model** — the 14 kernel entities from `../core-model/01-
  entities.md` (`Agent`, `Intent`, `Offer`, `Negotiation`, `Coalition`,
  `Mandate`, `Commitment`, `Fulfillment`, `Attestation`, `Market`,
  `ClearingMechanism`, `ServiceCategory`, `Principal`, `AgentProfile`).
- **Wire message formats** — the schemas in `../core-model/04-schema.md`,
  as a versioned, strictly-typed contract. Strict typing here is also the
  prompt-injection defense from `../technical-deep-dive/06-caveats-and-
  practical-realities.md` §3 — the two requirements reinforce each other.
- **Negotiation state machine** — the bounded offer/counter/commit/coalition
  lifecycle (`../core-model/02-generalized-flow.md`,
  `../technical-deep-dive/02`). Two deployments must agree on what
  "committed" means or cross-deployment transactions are undefined.
- **Mandate / authorization semantics** — how a `Principal` bounds an
  `Agent`'s authority (AP2-derived). A commitment authorized under a
  mandate on deployment A must be verifiable as validly-authorized by
  deployment B.
- **Identity model** — agents and principals identified by DIDs
  (decentralized identifiers), so identity is not owned by any single
  deployment. This is the linchpin of federation (`03`) and therefore
  core, not adapter.
- **The `ServiceCategory` extension interface** — the *contract* for how a
  vertical plugs in (`../core-model/03-extensibility-and-vertical-
  mapping.md`). The interface is core; the specific category schemas that
  implement it are Layer 2 packages (below).
- **Conformance rules** — the machine-checkable spec of "what a compliant
  implementation must do," enforced by a test suite
  (`../technical-deep-dive/06` §5, and `04-open-source-and-governance.md`).

**Everything in Layer 1 is versioned with explicit capability
negotiation.** A deployment advertises which core version and which
extensions it speaks (the way HTTP does content negotiation, or gRPC/
protobuf handle schema evolution), so a v1.2 network and a v1.4 network
can still find a common subset instead of failing. Without this, "open
protocol, many implementations" becomes "many incompatible dialects" —
the single most common way open standards rot.

## 3. Layer 2 — the adapters (what a deployer swaps for their own infra)

Each of these is a **port defined in Layer 1 with an interface, and an
implementation supplied per deployment.** This is the layer that makes
"bring your own cloud/infra" literally true.

| Adapter port | What a deployer swaps in | Precedent |
|---|---|---|
| **Storage** | Their own Postgres / DynamoDB / Spanner for `Market` shard state, holds, commitments, audit trail | k8s CSI; any DB-behind-a-repository-interface |
| **Payment rail** | UPI, PIX, FedNow/RTP, SEPA Instant, cards, or settle via AP2 — per region (`../technical-deep-dive/07` §3) | Stripe's payment-method abstraction |
| **Identity / attestation provider** | Which DID method, which credential issuers, which KYC/license-verification vendor (`../industries/` verticals each need different ones) | OIDC/SAML pluggable IdP |
| **Clearing mechanism** | Which of the four mechanisms from `../technical-deep-dive/04` a `Market` runs, and its implementation (posted-price, bilateral, sealed-bid double auction, combinatorial auction) | pluggable scheduler/policy engine |
| **Transport** | A2A over HTTP, gRPC, or an internal message bus, TLS/mTLS config | k8s CNI; gRPC transport plugins |
| **Category-schema packages** | The `intent_ext`/`offer_ext`/compatibility/evidence schemas for the verticals this deployment serves | Terraform providers; VS Code extensions |

The rule: **an adapter can change *how* something is done without changing
*what* crosses the wire.** Uber can store shard state in their own
Spanner and settle over their own payment stack, and a WhatsApp-hosted
network can use entirely different ones, and the two can still transact —
because the Layer 1 wire contract between them is identical regardless of
what's behind each side's adapters.

## 4. Layer 3 — deployer-owned (ops and policy)

Nothing in this layer is the protocol's business; it's where the deployer
runs and governs their instance:

- **Runtime/ops** — their Kubernetes/serverless/VMs, autoscaling of shards
  (`../technical-deep-dive/01` is the data-plane design they're scaling),
  observability, backups, SLAs.
- **Business policy** — which categories they enable, their fee (if any) on
  top of the protocol, their `default_autonomy_level` choices within the
  category floors, their supply-onboarding rules.
- **Whether to federate at all** (`03`) — a pure Layer-3 decision; a
  deployment is a private island until its operator opts in.

## 5. The reference stack (what "plug-and-play" actually ships as)

To make Layers 1-2 usable in a weekend, the open-source deliverable is not
just a spec PDF — it's:

- **A spec** (Layer 1, human- and machine-readable, versioned).
- **Reference adapter implementations** for the common cases (a Postgres
  storage adapter, a UPI + a Stripe payment adapter, a `did:web` identity
  adapter, the four clearing mechanisms, an A2A/HTTP transport) — so a
  deployer with standard infra runs out-of-the-box and only writes an
  adapter when they have something nonstandard.
- **SDKs** in a few languages for building agents against the protocol
  (the thing a provider's or consumer-platform's engineers actually code
  against).
- **Packaging** — container images + a Helm chart / operator, so
  `helm install` stands up a working single-tenant network on the
  deployer's own cluster.
- **The conformance test suite** — so a deployer (or a from-scratch
  reimplementer) can prove their deployment is spec-compliant and will
  interoperate (`04`).

The design test for this whole layering: **a competent team should be able
to stand up a private, working, single-vertical network on their own
cloud from the reference stack in days, writing zero protocol code and at
most one custom adapter — and have it be automatically capable of
federating later without re-architecting.** If standing up a private
network requires forking the core, Layer 1 is too big or the adapter
boundaries are in the wrong place.
