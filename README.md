# A2A-Native Marketplace Protocol

An open protocol for many-to-many, perishable-capacity marketplaces —
starting with intercity ride-sharing — where **consumer agents** and
**provider agents** (individual drivers, pooling operators, private
tour/charter buses, scheduled public transport, railway) discover each
other, negotiate terms, and commit on behalf of the humans they represent,
instead of a human manually scrolling listings and waiting on accept/reject.

Consumer agents can also cooperate with each other — pooling several
otherwise-unviable trip requests into one joint offer a provider will
actually accept — subject to human-approved comfort/compatibility
preferences. Price discovery runs through a neutral market-clearing layer
rather than free-for-all bilateral pricing, specifically to prevent
independent provider agents from converging on cartel-like pricing.

Builds on top of [A2A (Agent2Agent Protocol)](https://a2a-protocol.org)
for agent discovery/transport and [AP2 (Agent Payments Protocol)](https://cloud.google.com/blog/products/ai-machine-learning/announcing-agents-to-payments-ap2-protocol)
for payment authorization mandates. This repo defines the missing layer on
top of both: negotiation and marketplace semantics (intent, offer, counter,
coalition formation, commitment, fulfillment, reputation).

See [`docs/design.md`](docs/design.md) for the full design doc: problem
statement, prior-art comparison, protocol layering, message schemas, and
open caveats.

Ride-sharing is the motivating example, not the ceiling. See
[`docs/industries/`](docs/industries/) for five other industries worked
through in the same detail (home services, food & dining, freight &
logistics, home healthcare, event services), each testing a different
facet of the protocol — urgent vs. scheduled matching, time-slot vs.
vehicle capacity, provider-side vs. consumer-side pooling, and how far
agent autonomy should extend by default.

See [`docs/technical-deep-dive/`](docs/technical-deep-dive/) for the
engineering and economics questions underneath all of the above: matching
architecture at real M-provider × N-consumer scale, the mechanics of
consumer-agent coalition negotiation, how provider isolation is actually
enforced, which auction/bargaining mechanism price discovery uses and why,
an honest assessment of what (if anything) is defensible about an *open*
protocol, the toughest unresolved practical risks (including agent-security
threats like prompt injection between untrusted agents), and whether a
≤2%-of-transaction-value operating cost is realistically achievable.

See [`docs/core-model/`](docs/core-model/) for the industry-agnostic
core: one `Agent` entity (not separate consumer/provider types — "demand"
vs. "supply" is a *stance*, not a kind of agent), plus 13 other kernel
entities (`Intent`, `Offer`, `Negotiation`, `Coalition`, `Mandate`,
`Commitment`, `Fulfillment`, `Attestation`, `Market`, `ClearingMechanism`,
`ServiceCategory`, ...) and exactly one extension point
(`ServiceCategory`) that every vertical — travel included — plugs into as
registered data, never as a protocol change. This is the generalized
object model the travel-specific and industry-specific docs above are
each an instance of.

See [`docs/business-strategy/`](docs/business-strategy/) for whether
there's an actual business here: an honest look at when an individual
provider's agent can (and can't) compete with an incumbent platform —
Uber's on-demand dispatch and BookMyShow's fixed-inventory ticketing turn
out to be different competitive situations, not one — a scoring framework
for where this protocol fits well vs. poorly, who the paying customer
should actually be (infrastructure for providers and assistant platforms,
not a competing consumer app), a phased go-to-market for reaching scale
without spreading liquidity too thin, and a catalog of unresolved business
questions (governance, incumbent-copy risk, insurance, adoption
psychology) flagged rather than answered.

**Status:** early design draft, no implementation yet.
