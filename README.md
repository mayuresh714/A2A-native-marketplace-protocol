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

**Status:** early design draft, no implementation yet.
