# a2a-marketplace (Python)

An **open, business-neutral** implementation of the A2A-native marketplace
protocol: the matching, negotiation, coalition, and escrowed-settlement
machinery for agent-mediated marketplaces — with **zero runtime
dependencies** and a **ports-and-adapters** design so an operator (Uber,
BlaBlaCar, Zomato, OLX, …) plugs in their own infrastructure without forking
the core.

It implements the frozen v0 spec in [`../docs/spec/`](../docs/spec/) and
speaks the wire schemas in [`../schema/`](../schema/).

> Status: v0 / alpha. In-memory reference adapters + one reference category
> (intercity ride-pooling). The engine is the real, neutral core; the
> adapters are swappable.

## Why it's structured this way

The library is deliberately split along the layer model from
[`../docs/spec/02`](../docs/spec/02-layers-governance-security.md):

- **`engine.py` — the neutral mechanism (Layer A).** Runs the machine and
  holds *no policy*: it never ranks, never sets price, and doesn't know what
  a "ride" is, and it never decides a dispute's outcome. Per-request fraud
  filter → demand/supply queues → solo-first match → consumer coalition on
  failure (only after that intent's own wait timer expires) → a **staged
  `MatchProposal`** (notify both sides) → both sides approve + funds
  captured into platform custody → `Commitment` ("agreement, not final") →
  fulfillment window (variable duration) → dual-approval + evidence →
  settlement, or a dispute that freezes escrow until the operator's
  `DisputeResolver` resolves it.
- **`ports.py` — the pluggable interfaces (what an operator owns).**
  `Storage`, `RankingPolicy` (Layer B — ranking is *yours*, not the
  protocol's), `EscrowProvider`, `IdentityVerifier`, `RequestFraudFilter`,
  `Notifier`, `DisputeResolver` (Layer C policy), `Category`, `Clock`.
- **`adapters.py` — reference in-memory implementations** so it runs out of
  the box. Replace each with your own infra in production.
- **`categories/intercity.py` — a reference vertical.** The only file that
  knows what a ride is. New marketplace kind = new `Category`, engine
  unchanged.

## Install

```bash
cd python
pip install -e ".[dev]"      # editable, with pytest + ruff
```

## 60-second example

```python
from a2a_marketplace import dev_engine
from a2a_marketplace.models import partition_of

engine = dev_engine()        # in-memory adapters + intercity category
# ... submit offers and intents (see examples/demo_intercity.py) ...
proposals = engine.run_partition("intercity_travel", partition_of(corridor))
# a proposal auto-finalizes into a Commitment if BOTH sides' mandates/offers
# allow auto-commit; otherwise call engine.approve_proposal(proposal, side=...)
commitment = next(iter(engine.storage.commitments.values()))
fulfillment, settlement = engine.fulfill(
    commitment, consumer_approved=True, provider_approved=True, evidence=evidence)
```

Run the full worked scenario (three riders pooling into one Pune–Kolhapur
ride via a staged proposal requiring explicit approval, escrowed settlement,
and a second example showing a mid-window dispute freezing escrow):

```bash
python examples/demo_intercity.py
pytest -q
```

## How the principles show up in code

| Principle (`../docs/spec/01`) | In the code |
|---|---|
| P1 — consumers pool, providers don't | `Coalition.__post_init__` raises on `stance != DEMAND` |
| P3 — grouping keys / constraints / preferences | three separate fields on `Intent`; partition keyed only on grouping keys |
| P4 — fraud prevention | identity gate on `register_agent`; `RequestFraudFilter` on every `submit_intent`/`submit_offer`; mandate ceiling enforced *in code*, checked against each coalition member's own share, never the group total |
| P5 — collaborate on failure | `engine.run_partition` tries solo first, coalition only if solo fails |
| P6 — FIFO within partition | `Storage.demand_queue`/`supply_queue` return items sorted by `created_at` |
| P7 — transaction on match | an approved `MatchProposal` forms a `Commitment` |
| P8 — money only on dual approval + evidence | `engine.fulfill` releases escrow only if all three gates pass, and only if no dispute is open |
| P10 — ranking is the operator's | the engine never ranks; it calls the injected `RankingPolicy` |
| P11 — staged proposal, dual approval, platform custody | `run_partition` returns `MatchProposal`s, not `Commitment`s; `engine.approve_proposal(...)` captures funds and forms the `Commitment` only once both sides approve |
| P12 — time-boxed escalation | `Intent.solo_wait_seconds` / `collaboration_eligible_at()` gate when a coalition attempt is even tried |
| P13 — variable duration + mid-window disputes | `Commitment.fulfillment_window`; `engine.raise_dispute(...)` unconditionally freezes escrow; `engine.resolve_dispute(...)` delegates to the injected `DisputeResolver` (Layer C) |

## Extending it (the whole point)

Swap any port for your own. For example, your own ranking policy:

```python
class ByProviderRating:
    def rank(self, intent, candidates):
        return sorted(candidates, key=lambda o: -o_rating(o))  # your logic

engine = MarketplaceEngine(..., ranking=ByProviderRating(), ...)
```

Add a whole new vertical by implementing `ports.Category` (grouping,
`satisfies`, `price_for`, `compatible`, `verify_evidence`) — no engine
changes. That is what makes this a general marketplace substrate rather than
a ride-sharing app.

## License

Apache-2.0. Open protocol, open implementation — see
[`../docs/platform-architecture/04`](../docs/platform-architecture/04-open-source-and-governance.md).
