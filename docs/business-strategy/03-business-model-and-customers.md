# Business model and customers: what are we actually building, for whom

"How do we propose this model" and "what customers do we want to create"
are really one question: **who is the paying/adopting customer, and what
exactly are we selling them** — and the answer has to be consistent with
`../technical-deep-dive/05-moat-and-strategy.md`'s conclusion that trying
to own liquidity or become another closed platform contradicts this
project's own premise.

## 1. Three possible postures, and why only one fits

- **(A) Become the marketplace operator ourselves** — build the consumer
  app, build the provider app, run the whole graph. This directly
  recreates the closed-platform structure this project exists to move
  away from, requires the same capital-intensive, winner-take-most
  marketplace-bootstrapping fight incumbents already won once
  (`01-individual-vs-platform-competition.md`), and puts us in direct
  competition with Uber/BlaBlaCar/BookMyShow-style incumbents on their
  own terms. **Rejected.**
- **(B) Sell picks-and-shovels: operate the neutral protocol
  infrastructure (registry, clearing, attestation) and build lightweight
  provider-enablement tooling, without owning either side's brand or
  consumer relationship.** Matches `../technical-deep-dive/05`'s
  recommended moat (operate the neutral clearing/trust utility). **This
  is the right posture.**
- **(C) Build only a consumer-facing agent/app** — compete directly for
  end-user attention against ChatGPT, Gemini, and the Uber app itself.
  Worst possible position: enormous distribution cost, no differentiated
  advantage on the one thing that matters most to a consumer (a working,
  trusted booking flow, which incumbents already have), and it puts us in
  a race we have no natural right to win. **Rejected.**

## 2. The actual pitch: infrastructure, not a competing app

Position this as **"Stripe/Twilio for agent-native service
marketplaces"** — a fragmented, long-tail provider (an individual driver,
a plumber, a small tour-bus operator, a two-person catering business)
should be able to become instantly matchable and negotiable by any
consumer agent, including a consumer's own general-purpose AI assistant,
without building any of their own agent infrastructure. The same way
Stripe let a small merchant accept payments without building a payment
gateway, this protocol plus a reference implementation should let a small
provider become "agent-marketplace-ready" in minutes, not months.

This also directly answers the harder distribution question raised in
`01-individual-vs-platform-competition.md`: incumbents like Uber have
already struck bespoke integration deals with major assistant platforms
(Uber×OpenAI, `../design.md` §2). No decentralized protocol wins by
asking every consumer-agent platform to build a separate, bespoke
integration against thousands of individually fragmented providers one at
a time — that doesn't scale any better than the status quo. The pitch to
an assistant-platform vendor has to be **"integrate with us once, reach
every fragmented long-tail provider on the network"** — the one-to-many
bridge a bespoke per-incumbent deal can't offer, because there is no
single incumbent to strike a deal with in a genuinely fragmented vertical.

## 3. Two customer segments, deliberately in this order

### First customer: the provider (supply side)

Bootstrap supply first, not demand. This is the classic and
well-evidenced marketplace-bootstrapping sequence (Airbnb, OpenTable, and
most two-sided marketplaces seed the harder, more fragmented side first),
and it fits this project's own structure especially well: providers in
the target verticals (`02-market-fit-framework.md`'s high-scoring markets)
are underserved *today*, with real, immediate pain (`../industries/home-
services.md` §2's "losing paid time either being unreachable or
constantly context-switching" is a genuine, currently-unaddressed cost).
Give them:

- A lightweight provider-agent tool (mobile-first, minimal setup — the
  actual "agent" should mostly be invisible software running on their
  behalf, not something they configure or code) that plugs them into the
  registry/`Market` shard for their category.
- A clear, immediate value proposition independent of the demand side ever
  materializing at scale: better fill rates, less manual app-checking,
  eventually a materially lower take-rate than whatever aggregator they
  currently depend on.

Once a region/vertical has real, quality, differentiated supply on the
network, it becomes something worth a consumer-agent platform's
integration effort — supply liquidity is the thing that makes the second
customer segment want to show up.

### Second customer: the consumer-agent platform (the actual scale unlock)

Not the end consumer directly (see posture (C) above) — the company or
product that operates the consumer's day-to-day AI assistant (a major
lab's assistant, a regional assistant product, or a vertical SaaS
company's embedded agent). Their problem: building and maintaining
bespoke integrations against thousands of fragmented individual providers
doesn't scale, and doing it themselves recreates exactly the same
"one company owns the graph" pattern Uber×OpenAI represents today. Selling
them a single integration that reaches the whole registered-provider
network is the actual mechanism by which this protocol could reach
"billions of agents" (`04-scaling-to-billions-gtm-roadmap.md`) — it rides
on assistant platforms' existing consumer distribution rather than trying
to build a competing one.

## 4. Revenue model

Consistent with the ≤2%-of-transaction-value target
(`../technical-deep-dive/07-cost-economics-2-percent-target.md`): a thin,
per-cleared-transaction fee funding the registry, clearing/collusion-
monitoring, and attestation infrastructure — not a marketplace commission
on the Uber/BlaBlaCar model. Early on, before enough transaction volume
exists to make a pure per-transaction fee viable, a modest subscription
fee for provider-enablement tooling is a reasonable bridge (the same way
many infrastructure companies start with a flat SaaS fee before shifting
to usage-based pricing once volume justifies it) — but the target
end-state pricing model is transaction-based and thin, not seat-based or
commission-based, to stay consistent with the project's own stated reason
for existing.

## 5. What "customer we want to create" really means here

Not "convince more people to want rides" — that demand already exists and
is already well-served in the wrong markets (Uber) and manually
self-served in the right ones (BlaBlaCar-style intercity, informal
tradesperson referrals). The customer this project should deliberately
create is **the fragmented individual provider who currently has no
realistic path to the kind of matching efficiency a platform like Uber
enjoys, given a way to get it without surrendering 25-30% of every
transaction or their customer relationship to do so.** That's a genuinely
new category of customer relationship — infrastructure customer, not
platform-captive merchant — and it's the one this protocol is actually
positioned to create that didn't exist before.
