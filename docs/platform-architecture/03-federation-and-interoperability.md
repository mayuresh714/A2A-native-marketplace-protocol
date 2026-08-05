# Federation: islands vs. a network-of-networks

This is the hard distributed-systems core of the whole "many deployments"
idea, and the part most worth reasoning through carefully. If every
deployment (`02`) is a permanent island, this is just self-hostable
software and the grand vision ("a marketplace regardless of distribution
platform") collapses into a pile of disconnected walled gardens. Federation
is what turns N private networks into one addressable market — *optionally*,
without forcing anyone to give up control.

## 1. Start from the right precedents

Every large-scale "many independent operators, one interoperable system"
network solved the same problems. Steal from them rather than inventing:

| System | Independent unit | How they federate | What we borrow |
|---|---|---|---|
| **Email (SMTP)** | A mail server | Any server delivers to any other over a shared protocol; MX records for discovery | Anyone runs their own; federation is default-open over a shared wire format |
| **The Web / DNS** | A domain/server | Hierarchical, cached, lightly-rooted name resolution | Registry-of-registries as a DNS-like directory, not a central database (§4) |
| **BGP / the internet** | An autonomous system (AS) | Peering/transit announcements between ASes | Networks as autonomous systems that *choose* peers; no global controller |
| **Card networks (Visa/Mastercard)** | An issuing/acquiring bank | A neutral network + interbank settlement/netting with defined liability | Cross-network settlement and dispute rules (§5) |
| **Telecom roaming** | A carrier | Bilateral/multilateral roaming agreements + clearing houses | Opt-in agreements between operators, neutral clearing between them |
| **ActivityPub / Mastodon** | An instance | Server-to-server federation, per-instance moderation/defederation | Instances can refuse to federate with bad actors (§6) |

The through-line: **the independent unit stays sovereign; interoperability
is a protocol they opt into; and where money or trust crosses boundaries, a
neutral clearing/settlement layer appears between operators** (Visa between
banks, clearing houses between carriers). That last point is where
`../business-strategy/06-positioning-first-principles.md`'s "neutral
clearing utility" finally sits in its *natural* place — between networks,
not inside one.

## 2. The federation spectrum (not a binary)

```
 ISLAND ──────────────▶ BILATERAL PEERING ──────────▶ OPEN FEDERATION
 private network,        two networks agree to           any conformant
 no interop              interoperate (like a             network can
 (Uber day 1)           roaming agreement)               transact with any
                        (Uber ↔ a regional               other (like email)
                         bus network)
```

A deployment moves rightward only when its operator chooses to. Most start
as islands; some peer selectively; a fully open tier exists for those who
want maximum liquidity and accept less control over counterparties. Design
for all three — forcing open federation would kill enterprise adoption
(no serious platform federates its supply graph to unknown parties on day
one), and forbidding it would kill the network-of-networks vision.

## 3. Portable identity (the linchpin — this is why identity is in the core)

Federation is impossible if an agent's identity belongs to one network.
So identity must be **self-sovereign and network-independent**: agents and
principals are identified by **DIDs (Decentralized Identifiers)**, resolved
via a DID method the deployment supports (`01` puts the identity model in
the stable core exactly for this reason). A driver's agent identity is the
*same* DID whether it's transacting on Uber's network or a federated peer's
— no re-registration, no per-network account.

Consequence: an agent authenticated on network A can be *verified* by
network B without B trusting A's user database, because the DID + its
associated keys are cryptographically verifiable independently of any
network. This is the same reason DIDs exist in the W3C/SSI world — to
decouple identity from any single issuing platform.

## 4. Portable reputation (harder than identity — and easy to get wrong)

Reputation *wants* to be portable (a driver's track record shouldn't be
trapped in one network — that's the anti-lock-in promise from
`../technical-deep-dive/05`), but naive portability is dangerous.

- **Mechanism: Verifiable Credentials (VCs).** An `Attestation`
  (`../core-model/01-entities.md` §11) is a signed VC — "issuer X asserts
  claim Y about subject-DID Z" — verifiable by anyone who trusts issuer X,
  on any network. License verifications, insurance status, and aggregate
  ratings all become portable signed credentials rather than rows in one
  network's database.
- **The trust-of-the-issuer problem.** Network B verifying a VC still has
  to decide *whether it trusts the issuer.* This needs a **trust
  framework**: a set of recognized issuers/roots that networks agree on —
  structurally identical to the Certificate Authority trust model in
  TLS/PKI, or to eIDAS trust lists. Running that trust registry neutrally
  is another natural inter-network-utility role (§7).
- **The context problem (the subtle one).** A 5-star reputation earned on a
  low-stakes network (casual food-delivery pooling) must not silently
  confer trust on a high-stakes one (home-healthcare, freight). So a
  portable reputation credential must carry **provenance and context**
  (which network, which category, what volume, over what period), and the
  *consuming* network decides how much weight to give it — never an
  automatic global score. This mirrors how credit/reputation signals are
  contextual in the real world, and it's a genuine design nuance, not a
  detail: unqualified global reputation portability is both gameable
  (`../technical-deep-dive/02` §5 Sybil/reputation attacks now cross
  network boundaries) and unsafe.

## 5. Cross-network discovery and settlement

### Discovery — a DNS-like registry-of-registries

When a consumer agent on network A wants supply that might live on network
B, something has to tell it B exists and serves that category/region. Three
options, matching the §1 precedents:

- **Central directory** — simplest, but a central chokepoint that
  contradicts "no one owns the graph."
- **Peer gossip (BGP-style)** — fully decentralized, networks announce
  categories/regions to peers; complex, eventually-consistent.
- **DNS-like federated directory (recommended)** — a lightly-rooted,
  cached, hierarchical directory of networks and the categories/regions
  they serve. No single server holds it all, resolution is cached, the
  root is minimally governed (`04`). This is the same shape that let the
  web scale without a central registry-of-everything, and it's the right
  balance of decentralization and simplicity here.

### Settlement — interbank-style, with a neutral clearer

When consumer(network A) transacts with provider(network B):

- **Whose payment rail, whose fee, who bears dispute liability?** These are
  exactly the questions interbank settlement and telecom roaming already
  answer: a defined **cross-network settlement protocol** with netting and
  explicit liability/dispute rules between operators.
- **This is the strongest argument for a neutral inter-network clearer.**
  A single network can clear its *own* internal transactions
  (`../technical-deep-dive/04`), but cross-network settlement between two
  self-interested operators is precisely where a neutral third party is
  both necessary and trusted — Visa's actual role between banks. It's also
  where the anti-collusion reference-price function
  (`../design.md` §7) has to operate at the inter-network level, since
  price signals now span operators.

## 6. Trust, abuse, and defederation

Federation opens attack surface — a malicious or lax network could inject
fake supply, fake reputation, or bad actors into peers. Borrow Mastodon/
email's answer: **networks can refuse to federate (defederate) with peers
that don't meet trust/moderation standards**, and the trust framework (§4)
gates which networks/issuers are recognized. Conformance certification
(`04`) is the entry ticket; ongoing behavior (dispute rates, fraud
signals) can get a network quarantined or defederated. This is a
governance function, not just a technical one — the same conclusion the
intra-network collusion-monitoring reached (`../design.md` §7), now one
level up.

## 7. Where the neutral operator actually sits (the payoff)

Pulling §3-6 together resolves the positioning tension in
`../business-strategy/06` cleanly. The neutral operator's product is the
**inter-network layer**:

- the **identity/trust roots** and the trust-framework registry (§3-4),
- the **DNS-like discovery directory** root (§5),
- the **cross-network settlement + anti-collusion clearing** (§5),
- **conformance certification** (§6, `04`).

None of that lives *inside* any deployment — every deployment is free to
self-host and never touch it, staying a private island. It only becomes
necessary, and worth paying for, at the moment two networks want to
interoperate — which is exactly the seat a neutral party can hold
credibly and profitably (Visa between banks, a clearing house between
carriers), and exactly the seat `../business-strategy/06` was looking for
but had placed awkwardly inside a single global network. Federation is
what puts it in the right place.

## 8. Honest open problems

- **Bootstrapping the trust framework** — who are the initial recognized
  roots, and how is that not just re-centralization under a friendlier
  name? Unresolved; ties directly to `04`'s governance question.
- **Cross-network dispute resolution at scale** — clear rules on paper
  (§5) are one thing; adjudicating a cross-operator dispute where each
  side's audit trail lives in a different deployment is genuinely hard and
  not fully designed.
- **Reputation-portability gaming** — §4's context-carrying mitigations
  reduce but don't eliminate cross-network Sybil/reputation laundering; it
  needs real adversarial modeling before a high-stakes vertical federates.
- **Incentive to federate** — a dominant network with its own deep
  liquidity may rationally *refuse* to federate to protect its moat
  (the same embrace-vs-open tension as `../technical-deep-dive/05` §1),
  which could leave federation to smaller players and fragment the market
  anyway. Whether federation actually happens is a strategic/economic
  question, not just a technical-capability one.
