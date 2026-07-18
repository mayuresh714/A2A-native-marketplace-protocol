# Technical deep dive

`../design.md` establishes the protocol shape. `../industries/` shows it
applies beyond travel. This folder answers the harder engineering and
economics questions that come up the moment you ask "okay, but how does
this actually run at scale, with real money, against real adversaries":

| # | File | Question it answers |
|---|---|---|
| 1 | [`01-scale-and-matching-architecture.md`](01-scale-and-matching-architecture.md) | With M providers and N consumers, matching is naively O(M×N) per window — how is this actually kept tractable at city/national scale? |
| 2 | [`02-consumer-collaboration-protocol.md`](02-consumer-collaboration-protocol.md) | Can consumer agents genuinely collaborate to make joint counter-offers — and what does that protocol look like mechanically, not just conceptually? |
| 3 | [`03-provider-isolation-and-discovery.md`](03-provider-isolation-and-discovery.md) | Providers are mutually unknown by default — how is that isolation actually enforced, not just assumed? |
| 4 | [`04-price-discovery-mechanism-design.md`](04-price-discovery-mechanism-design.md) | Exactly how does price discovery work — what mechanism, borrowed from where, and why? |
| 5 | [`05-moat-and-strategy.md`](05-moat-and-strategy.md) | What is the actual, defensible moat of an *open* protocol — honestly, not as a pitch? |
| 6 | [`06-caveats-and-practical-realities.md`](06-caveats-and-practical-realities.md) | What are the toughest, least-solved problems, including ones not yet raised (agent-security/prompt-injection, Sybil cost, interoperability)? |
| 7 | [`07-cost-economics-2-percent-target.md`](07-cost-economics-2-percent-target.md) | Is an all-in operating cost of ≤2% of transaction value actually achievable, and what has to be true for it to hold? |

## How to read these

These are working-through-the-hard-parts documents, not settled
specifications — several conclusions in here (the price-discovery
mechanism choice, the cost target's feasibility) are explicitly marked as
"needs validation," not decided. Where a claim rests on an existing,
well-studied idea from another field (auction theory, ad-exchange
architecture, market microstructure, payments), that's cited so it can be
checked rather than taken on faith.
