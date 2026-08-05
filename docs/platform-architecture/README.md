# Platform architecture: protocol as a self-hostable, federatable substrate

Everything before this folder implicitly assumed **one network, one
operator** — a single registry/clearing utility that everyone joins. This
folder answers a different question the project has to get right if it's
going to be open source and plug-and-play:

> **What if the protocol is a substrate that anyone can deploy to run
> their *own* agentic marketplace — Uber runs a private intercity network,
> OLX runs one for classifieds, WhatsApp embeds one, Amazon another — each
> self-hosted on their own cloud, and (optionally) able to interoperate?**

That reframes the whole thing from "a marketplace we operate" to "an open
protocol + reference stack others deploy," with an optional network-of-
networks on top. It doesn't contradict the positioning in
`../business-strategy/06-positioning-first-principles.md` — it *sharpens*
it: the open-source substrate is the adoption engine (the Linux/Postgres/
Kubernetes layer that gets everywhere precisely because it's free and
self-hostable), and the neutral **inter-network** clearing/trust/discovery
layer is the managed business (the thing that only makes sense operated by
a neutral party sitting *between* networks, not inside any one of them —
which is a far more natural seat for a neutral operator than the old
"one global network" framing ever was).

## The two ideas that make this work

1. **Ports-and-adapters core** (`01`). A small, stable, versioned open
   protocol + a set of pluggable interfaces (storage, payment rail,
   identity/attestation, clearing mechanism, transport, category schemas).
   A deployer brings their own implementations behind those interfaces —
   the same way Kubernetes defines CSI/CNI/CRI and lets the ecosystem ship
   drivers, or Terraform defines a provider interface. This is what makes
   "plug-and-play, self-host on your own infra" real rather than a slogan.

2. **Opt-in federation** (`03`). Every deployment starts as an island — a
   private, walled-garden network, which is exactly what a first adopter
   like Uber actually wants. Interoperability between networks is a
   *separate, opt-in layer* built on portable identity (DIDs), portable
   reputation (verifiable credentials), a DNS-like registry-of-registries
   for cross-network discovery, and an interbank-style settlement layer for
   cross-network transactions. Nobody is forced to federate; the ones who
   do unlock shared liquidity. This is how the internet, email, and card
   networks all actually scaled — private autonomous systems that chose to
   peer.

## Files

| # | File | System-design question |
|---|---|---|
| 1 | [`01-layered-architecture.md`](01-layered-architecture.md) | What exactly is the stable open core vs. a pluggable adapter vs. deployer-owned ops? The ports-and-adapters contract that makes it self-hostable. |
| 2 | [`02-deployment-topologies.md`](02-deployment-topologies.md) | The Network-as-a-Service spectrum: fully-managed multi-tenant ↔ dedicated managed ↔ fully self-hosted BYO-cloud. Control plane vs. data plane, tenant isolation, and worked deployments for Uber / OLX / WhatsApp / Amazon. |
| 3 | [`03-federation-and-interoperability.md`](03-federation-and-interoperability.md) | Islands vs. network-of-networks. Portable identity/reputation, cross-network discovery, cross-network settlement, and the neutral inter-network layer — the hard distributed-systems core of the whole idea. |
| 4 | [`04-open-source-and-governance.md`](04-open-source-and-governance.md) | Licensing (open-core, permissive vs. protective), foundation/consortium governance, conformance certification to stop fragmentation, and how open-sourcing the core reconciles with having any moat at all. |

## The framing to hold onto

Separate three things that the "one network" view kept mushing together:

- **The protocol** — an open spec. Free. Its job is ubiquity.
- **The reference stack** — an open-source implementation of that spec you
  can `docker run` / `helm install` on your own cloud. Its job is making
  adoption a weekend, not a quarter.
- **The inter-network utility** — the optional, neutral, managed layer for
  federation (identity roots, reputation verification, cross-network
  settlement, anti-collusion across networks). Its job is being the one
  seat a neutral operator can credibly and profitably hold.

A deployer can take the first two and never touch the third (a private,
self-hosted, non-federated network). The third only earns its keep the day
two networks want to transact with each other — which is exactly when a
neutral party between them becomes worth paying for.
