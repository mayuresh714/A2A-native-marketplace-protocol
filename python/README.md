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
  a "ride" is. Partition → FIFO queue → solo-first match → consumer coalition
  on failure → commitment + escrow → dual-approval + evidence → settlement.
- **`ports.py` — the pluggable interfaces (what an operator owns).**
  `Storage`, `RankingPolicy` (Layer B — ranking is *yours*, not the
  protocol's), `EscrowProvider`, `IdentityVerifier`, `Category`, `Clock`.
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
commitments = engine.run_partition("intercity_travel", partition_of(corridor))
fulfillment, settlement = engine.fulfill(
    commitments[0], consumer_approved=True, provider_approved=True, evidence=evidence)
```

Run the full worked scenario (three riders pooling into one Pune–Kolhapur
ride, then escrowed settlement):

```bash
python examples/demo_intercity.py
pytest -q
```

## How the ten principles show up in code

| Principle (`../docs/spec/01`) | In the code |
|---|---|
| P1 — consumers pool, providers don't | `Coalition.__post_init__` raises on `stance != DEMAND` |
| P3 — grouping keys / constraints / preferences | three separate fields on `Intent`; partition keyed only on grouping keys |
| P5 — collaborate on failure | `engine.run_partition` tries solo first, coalition only if solo fails |
| P6 — FIFO within partition | `Storage.queued_intents` returns intents sorted by `created_at` |
| P7 — transaction on match | a match forms a `Commitment` |
| P8 — money only on dual approval + evidence | `engine.fulfill` releases escrow only if all three gates pass |
| P4 — fraud prevention | identity gate on `register_agent`; mandate ceiling enforced *in code* |
| P10 — ranking is the operator's | the engine never ranks; it calls the injected `RankingPolicy` |

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
