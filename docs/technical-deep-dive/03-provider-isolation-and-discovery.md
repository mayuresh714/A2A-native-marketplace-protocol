# Provider isolation and discovery

Confirming the premise: yes, by default, provider agents are mutually
unknown and unable to see each other. This isn't just an incidental
starting assumption — it's a deliberate architectural choice, worth
stating explicitly because it does real work for the rest of the design.

## 1. Why isolation is deliberate, not incidental

- **It shrinks the collusion surface.** The single biggest systemic risk
  identified in `../design.md` §7 is independent provider agents
  converging on inflated pricing. That's structurally much harder if a
  provider agent literally cannot see what other providers are currently
  offering on the same route/time — sealed bids are a standard
  anti-collusion mechanism in auction design precisely because visibility
  into competitors' positions is what coordination (explicit or
  algorithmic) requires.
- **It matches real-world legal independence.** Most providers in this
  model are separate, unaffiliated businesses (individual drivers, small
  firms, different companies entirely). A design that gave them visibility
  into each other's live pricing would itself resemble the kind of
  information-sharing arrangement that antitrust frameworks scrutinize
  between competitors — the protocol isolating them by default is closer
  to *compliance-by-construction* than an arbitrary restriction.
- **It reduces integration burden.** Providers integrate once, against the
  shared protocol/registry — never against each other. This is what makes
  the market open to new entrants without negotiating bilateral
  integrations with every incumbent competitor, which is exactly the
  closed-platform pattern this project is trying to avoid recreating.

## 2. How isolation is technically enforced (not just assumed)

Isolation has to be an access-control property of the registry, not a
promise providers are trusted to honor:

- **Two distinct read paths out of the registry:**
  - *Consumer-facing reads* — a querying consumer (or coalition) agent
    sees candidate offers relevant to its intent, including which specific
    provider made each one.
  - *Provider-facing reads* — a provider agent can query aggregated,
    anonymized market signals only (the reference price band and demand
    heatmap from `04-price-discovery-mechanism-design.md`) — never another
    individual provider's live offer, identity, or specific terms.
- This needs to be enforced the way row-level security or scoped API
  tokens enforce it in any multi-tenant system — a provider agent's
  credentials simply don't authorize the query that would return another
  provider's live entry. It shouldn't be a client-side convention that a
  well-behaved implementation happens to follow; a differently-implemented
  or malicious provider agent must be structurally unable to retrieve it,
  not merely asked not to.
- **Sealed submission for the price-clearing mechanism** (§4 of the
  companion doc) follows the same principle at the mechanism-design
  level: reservation prices are submitted sealed, and the clearing
  algorithm is the only party that ever sees the full set — individual
  bids are never revealed to other bidders, win or lose.

## 3. What providers *can* see

Isolation from each other doesn't mean isolation from all signal — a
provider agent needs enough market information to price and schedule
sensibly, just not competitor-specific information:

- **Aggregate reference price band** for its route/time-bucket (trailing
  historical percentile, not live competitor bids — see companion doc §5).
- **Aggregate demand signal** (how many open consumer intents exist for
  this corridor/time-bucket, without attribution to which consumer or
  what any of them individually offered) — enough to inform "should I
  offer capacity on this route right now," not enough to reverse-engineer
  another specific provider's position.
- **Its own historical performance** (acceptance rate, fill rate,
  reputation trend) — self-data only.

## 4. The deliberate exception: disclosed, opt-in coalitions

`../industries/event-services.md` describes standing vendor coalitions
(venue + caterer + photographer pre-coordinating). This is real,
legitimate, and explicitly *not* covered by default isolation — but it
has to be handled as a distinct, visible object, not a loophole that
quietly erodes the default:

- A standing coalition is a separate, explicitly-registered entity (a
  named group of provider agents that have opted in to joint visibility
  with each other), not an emergent side-channel.
- Consumers must be able to see that a bundle offer comes from a
  coordinating group (`../industries/event-services.md` §8's transparency
  requirement) rather than mistaking it for an independently-assembled
  selection.
- Isolation-breaking is therefore **opt-in, disclosed, and auditable** —
  the default stays isolated, and any deviation from that default is a
  visible, logged exception, not a silent one. This is the same principle
  `../design.md` §7 uses for collusion monitoring generally: correlated
  behavior between providers should always be either explained by a
  disclosed coalition or flagged as suspicious — there shouldn't be a
  third, invisible category.

## 5. Reputation without cross-visibility

Reputation naturally wants some comparative signal ("how do I compare to
other providers on this route"), which is in tension with isolation. The
resolution: reputation is computed centrally from consumer-side feedback
and published *only* as an attestation attached to a provider's own offer
(a score/badge the consumer sees), plus an aggregate market-level signal
(e.g., "average rating for verified individual drivers on this corridor is
4.6") — never as a queryable list of competitors' individual scores. A
provider can learn where it stands relative to the market distribution
without learning who specifically is beating it or by how much — the same
level of granularity a seller on most reputable marketplaces gets today,
deliberately not more.
