# Deployment topologies: the Network-as-a-Service spectrum

Given the layered architecture in `01`, a deployer can consume it at very
different levels of "managed vs. self-run." This doc lays out that
spectrum, the control-plane/data-plane split that makes it work, the
tenant-isolation problem, and worked deployments for the exact examples
raised — Uber, OLX, WhatsApp, Amazon.

## 1. The spectrum (three points, one dial)

```
 fully managed  ◀──────────────────────────────────────▶  fully self-hosted
 (we run it)                                              (they run it, BYO cloud)

 ┌──────────────┐      ┌──────────────────┐      ┌────────────────────────┐
 │ MULTI-TENANT  │      │ DEDICATED /       │      │ SELF-HOSTED             │
 │ SaaS          │      │ SINGLE-TENANT     │      │ (open-source stack on   │
 │ (shared data  │      │ MANAGED           │      │  their own infra)       │
 │  plane, many  │      │ (isolated instance│      │                         │
 │  tenants)     │      │  we operate for   │      │ we may sell support/    │
 │               │      │  them)            │      │ certification only      │
 └──────────────┘      └──────────────────┘      └────────────────────────┘
   lowest ops for         isolation + managed        max control & data
   the deployer,          convenience, higher         residency, they own
   least control          cost                         the ops burden
```

This is the standard enterprise-infra packaging ladder (the same one
Elastic, GitLab, HashiCorp, Confluent all offer: cloud SaaS → dedicated →
self-managed). The open-source core (`01`, `04`) is what makes the
right-hand end honest — a deployer worried about lock-in or data
residency can always take the self-hosted path, which is precisely why
they'll trust the managed one.

## 2. Control plane vs. data plane (the split that makes NaaS work)

Regardless of where on the spectrum a deployment sits, cleanly separate:

- **Data plane** — the per-transaction runtime: `Market` shards, candidate
  generation, negotiation, holds, commitment, settlement. Latency- and
  volume-sensitive (`../technical-deep-dive/01`). In a self-hosted
  deployment this runs entirely on the deployer's infra; in managed, on
  ours; in dedicated, on ours but isolated to them.
- **Control plane** — management and configuration: category registration,
  policy, key/identity management, dashboards, billing, deployment
  lifecycle. Low-volume, human-driven.

Why the split matters for NaaS specifically: it lets you offer a **managed
control plane over a self-hosted data plane** — the deployer keeps all
transaction data and traffic on their own cloud (data residency,
sovereignty, no egress of sensitive negotiation/PII to us), while we
manage the fiddly configuration/upgrade/observability control plane as a
service. This "managed control plane, customer-hosted data plane" pattern
is exactly how modern data infra (Confluent, Databricks, various
"bring-your-own-cloud" offerings) squares managed convenience with
enterprise data-control demands — and it's likely the sweet spot for
large, security-conscious adopters like the ones in §5.

## 3. Tenant isolation (a distinct axis from market isolation)

Two isolation concerns exist and they're easy to conflate:

- **Intra-network market isolation** (already designed,
  `../technical-deep-dive/03`) — within one network, same-stance agents
  can't see each other's live bids. This is about collusion/competition.
- **Cross-tenant network isolation** (new here) — Uber's private network
  and OLX's private network must not see each other's agents, supply,
  data, or traffic at all, unless they explicitly federate (`03`). This is
  about multi-tenancy.

Options for the second, cheapest-to-strongest:

| Isolation model | Mechanism | Trade-off |
|---|---|---|
| **Logical (namespace) isolation** | One shared data plane, tenant-scoped partitioning of storage/shards + row-level security | Cheapest to operate; strongest blast-radius and compliance concerns; fine for small tenants |
| **Dedicated instance** | Separate deployment (own DB, own compute) per tenant, we operate it | Strong isolation, higher cost — the "dedicated managed" spectrum point |
| **Self-hosted** | Tenant runs their own deployment on their own cloud | Total isolation by construction; tenant owns the ops |

The default recommendation for any large or regulated tenant is dedicated
or self-hosted — logical multi-tenancy is a reasonable entry tier for
small deployers but a poor fit for a company that considers its supply
graph a competitive asset (all of §5's examples do).

## 4. What a deployer brings vs. gets

In this model a distribution platform brings the two things they uniquely
have, and gets the two things they don't want to build:

- **They bring:** (a) their consumer distribution — the app/surface their
  users already open, which becomes the demand-side agent front-end; (b)
  their existing supply relationships or category expertise.
- **They get:** (a) the whole negotiation/pooling/matching/clearing
  machinery as deployable infra instead of a multi-year build; (b)
  optional future access to *other networks'* liquidity via federation
  (`03`) without giving up control of their own.

## 5. Worked deployments

### Uber — private intercity network (single-tenant, likely self-hosted)

Uber deploys a private instance for a vertical they *don't* serve well
today (intercity, not their on-demand core — consistent with
`../business-strategy/01-individual-vs-platform-competition.md` §2 that
intercity, not city dispatch, is where this mechanism fits). They register
the `intercity_travel` `ServiceCategory`, bring their existing drivers as
supply agents and their existing rider app as the demand front-end, run it
on their own cloud with their own payment stack behind the payment adapter.
It's a walled garden — no federation needed on day one. Notably this turns
Uber from "incumbent to route around" into "adopter of the open infra for a
new vertical," a genuinely different and non-adversarial relationship than
the business-strategy docs assumed — because they're deploying it inside
their own distribution, not being disintermediated by it.

### OLX — classifieds / second-hand goods and services network

OLX registers different `ServiceCategory` packages (local services,
second-hand goods with negotiation — classifieds are *natively*
negotiation-heavy, a strong fit per `../business-strategy/02-market-fit-
framework.md`'s negotiation-surface dimension). Same substrate, entirely
different category schemas and matching keys — no core change
(`../core-model/03`). Their existing buyer/seller base becomes the two
stances.

### WhatsApp — embedded network as a conversational front-end

WhatsApp embeds the demand-side agent directly in chat (their distribution
*is* the messaging surface). They might run a lighter deployment focused on
being a consumer-agent front-end into *federated* supply (`03`) rather than
hosting deep supply themselves — i.e. they lean on federation early
precisely because their asset is distribution/reach, not supply
relationships. This is the case where federation matters on day one, unlike
Uber's.

### Amazon — services marketplace adjacent to goods

Amazon deploys for local/home services (an existing but under-optimized
part of their business), using their identity/payments/trust infrastructure
behind the respective adapters — one of the cases where a deployer's own
attestation and payment infra is a strength they plug in, rather than
something they need from us.

## 6. The cross-cutting insight

The same open-source substrate serves all four despite radically different
businesses, because each one only supplies (a) category schemas, (b)
adapters for their own infra, and (c) a deployment topology choice — none
of which touch the core (`01` Layer 1). That's the entire payoff of the
ports-and-adapters design: **the marketplace is deployer-specific; the
protocol underneath is identical**, which is exactly the precondition for
these networks to later federate into shared liquidity (`03`) instead of
being permanent islands.
