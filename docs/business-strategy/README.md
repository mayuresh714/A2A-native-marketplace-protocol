# Business strategy

Everything before this folder answers "can this be built and does it hold
together technically." This folder answers the harder question: **is
there an actual business here, who is it for, and where does it win or
lose against the platforms that already exist** — Uber, BookMyShow,
BlaBlaCar, and whatever else already occupies a given vertical.

| # | File | Question it answers |
|---|---|---|
| 1 | [`01-individual-vs-platform-competition.md`](01-individual-vs-platform-competition.md) | Can an individual driver's agent actually compete with Uber? Can a single theatre's agent compete with BookMyShow? (Short answer: these are two different competitive situations, not one — worked through in detail.) |
| 2 | [`02-market-fit-framework.md`](02-market-fit-framework.md) | A scoring framework — negotiation surface, supply fragmentation, existing-platform efficiency, assistant-integration risk — applied to score where this protocol fits well vs. where it doesn't, including against Uber and BookMyShow directly. |
| 3 | [`03-business-model-and-customers.md`](03-business-model-and-customers.md) | What is the actual product, who pays, and — the sharper question — which customer should this project deliberately create first: the provider, the consumer, or the assistant platform sitting between them? |
| 4 | [`04-scaling-to-billions-gtm-roadmap.md`](04-scaling-to-billions-gtm-roadmap.md) | "Billions of agents" from a go-to-market angle, not a compute angle — the technical sharding in `../technical-deep-dive/01` makes scale computationally cheap, but liquidity and trust don't scale that way; this lays out the actual sequencing. |
| 5 | [`05-open-business-issues.md`](05-open-business-issues.md) | A consolidated catalog of unresolved business questions — governance, incumbent-copy risk, adoption psychology, insurance, first-market choice — flagged rather than answered, since several genuinely don't have answers yet. |

## The one honest framing to hold onto across all five

This protocol is not a better Uber. Applying it to Uber's actual
business (on-demand, hyper-local, low-negotiation-value city dispatch) is
picking a fight on ground where centralization is *legitimately* the
better mechanism, not just an entrenched incumbent
(`../design.md` §4 already established this — Uber's posted-price model
is a good answer to that specific problem). The business case here is
strongest exactly where a dominant platform **hasn't** already solved
matching efficiently — fragmented, negotiable, currently-badly-served
markets — and weakest wherever one already has. Confusing the two is the
single most likely way to waste this project's early effort on the wrong
fight.
