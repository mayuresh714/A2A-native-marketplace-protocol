# A2A-Native Marketplace Protocol

An open protocol for two-sided, perishable-capacity marketplaces —
starting with intercity ride-sharing — where a **consumer agent** and a
**provider agent** discover each other, negotiate terms, and commit on
behalf of the humans they represent, instead of a human manually scrolling
listings and waiting on accept/reject.

Builds on top of [A2A (Agent2Agent Protocol)](https://a2a-protocol.org)
for agent discovery/transport and [AP2 (Agent Payments Protocol)](https://cloud.google.com/blog/products/ai-machine-learning/announcing-agents-to-payments-ap2-protocol)
for payment authorization mandates. This repo defines the missing layer on
top of both: negotiation and marketplace semantics (intent, offer, counter,
commitment, fulfillment, reputation).

See [`docs/design.md`](docs/design.md) for the full design doc: problem
statement, prior-art comparison, protocol layering, message schemas, and
open caveats.

**Status:** early design draft, no implementation yet.
