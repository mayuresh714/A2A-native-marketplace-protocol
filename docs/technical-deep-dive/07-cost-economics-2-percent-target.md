# Cost economics: is ≤2% all-in achievable?

The target: total operating cost of this protocol's infrastructure should
be ≤2% of transaction value — comparable to a payment-processing cost, not
a platform-commission. This doc breaks that down into components and
checks each one against reality, rather than asserting the target as
given.

## 1. What "2%" should actually be compared against

Two very different categories exist today, and the target only makes
sense against one of them:

- **Payment processing alone:** card network interchange + processing
  typically runs ~2-3% globally. This is the closest existing comparison
  to "just moving the money," and roughly the ceiling this project should
  be measuring against for that one component.
- **UPI (India) — a directly relevant precedent given this project's
  reference geography:** India's UPI real-time payment rail runs at
  near-zero merchant discount rate by regulatory design. This matters a
  lot here specifically: it's existing proof that a near-zero-cost,
  massive-scale, real-time payment rail is achievable when the
  infrastructure is built as a standardized public utility rather than a
  card-network-style toll — directly supportive of this project's own
  "infrastructure, not rent-extraction" premise, and it means an
  India-first rollout starts with a materially cheaper payment leg than a
  card-heavy market would.
- **Marketplace platform commissions — the wrong comparison to beat:**
  Uber's take rate runs roughly 25-30%; BlaBlaCar's roughly 18-21%. These
  aren't transaction-processing cost, they're platform profit margin —
  categorically different from what this project is trying to charge for.
  2% is not "cheaper than Uber's commission" (that's a low bar, ~10-15x
  lower); it's specifically "roughly in line with pure payment processing
  plus a thin infrastructure fee, with the 20-30% commission layer removed
  entirely." That's the actual claim being made, and it should be stated
  that precisely rather than vaguely as "cheaper."

## 2. Breaking the 2% budget into components

Illustrative allocation, not a committed pricing model:

| Component | Rough share of a 2% budget | Key lever |
|---|---|---|
| Payment rail | 0-1% | Which rail is used, by far the highest-leverage single decision (§3) |
| Matching/negotiation compute | should be a small fraction of a cent per transaction | Whether negotiation logic is LLM-call-per-message or cheap deterministic logic (§4) — the single most likely place to blow the budget by accident |
| Trust/attestation/fraud amortization | the biggest real-world cost driver in payments generally | Fraud rate, which depends on reputation-system maturity (§5) |
| Market-clearing/collusion-monitoring operations | small per-transaction, real fixed cost | Amortizes down with volume, like exchange economics |
| Dispute resolution / support | hardest to keep thin | How automatable disputes are given the audit trail (§6) |

## 3. Payment rail: the highest-leverage decision

If the default payment path routes through card networks, 2-3% is
consumed by that leg alone, leaving essentially nothing for every other
component — the budget is blown before matching, trust, or clearing costs
are even considered. **The protocol needs to default to low-cost
real-time payment rails per region** (UPI in India, PIX in Brazil,
FedNow/RTP in the US, SEPA Instant in the EU) and treat card payment as an
explicit, separately-priced fallback — not silently absorb card cost into
the advertised 2% figure. This is a design requirement for the AP2
payment-mandate integration (`../design.md` §9), not just a business
decision: which rails an implementation supports materially determines
whether the cost target is even reachable in that market.

## 4. Matching/negotiation compute: the easy-to-miss budget killer

Concrete arithmetic, using the running example from the main design doc: a
₹550 ride, 2% budget = **₹11 total**, covering every component in the
table above, not just compute. If a consumer agent's negotiation logic
invokes a frontier LLM API call for every offer/counter-offer round — and
a multi-round bilateral negotiation (`04-price-discovery-mechanism-
design.md` §1b) plus coalition formation
(`02-consumer-collaboration-protocol.md`) could easily involve 5-10 such
calls per booking — retail LLM API pricing for even a few calls at typical
per-request token volumes can already approach or exceed that entire ₹11
budget, before payment processing, trust infrastructure, or dispute
handling are paid for at all.

**Architectural consequence, not just a cost footnote:** negotiation logic
(candidate filtering, price-fit scoring, time-window intersection,
mandate-boundary checks, auction clearing) must default to cheap,
deterministic computation — the kind of arithmetic and rule evaluation
worked out in `01-scale-and-matching-architecture.md` and
`02-consumer-collaboration-protocol.md` §4 — not a per-message LLM call.
LLM usage should be reserved for the parts that actually need language
understanding: the human-facing conversational layer (taking the initial
request, presenting a final recommendation, handling a clarifying
question), amortized once per booking session, not once per negotiation
round. This is a direct, quantitative argument for why the protocol's
negotiation objects need to be structured/computable (as already designed)
rather than left as open-ended agent-to-agent conversation — cost
discipline, not just security (`06-caveats-and-practical-realities.md`
§3), pushes the same direction.

## 5. Trust/fraud cost: the maturity curve problem

In real payment systems, a substantial share of that 2-3% processing cost
funds fraud and chargeback risk absorption, not just payment rail
mechanics. This project's equivalent cost driver is fraud/dispute rate,
which depends directly on how good the reputation/attestation system
(`03-provider-isolation-and-discovery.md` §5, `../design.md`'s
Trust/Attestation service) actually is — and that system only gets good
with real transaction history. This is a genuine chicken-and-egg cost
problem: **early in a market's life, before reputation data is deep,
fraud/dispute costs will likely run higher than 2% can absorb**; the 2%
target is more realistically a **maturity-state target**, reached as
volume and verified reputation history accumulate, not a day-one
guarantee. A pilot should budget for a materially higher early cost ratio
(plausibly 4-6%, as a rough directional estimate, not a committed number)
and treat convergence toward 2% as a thing that has to be demonstrated
over time against real fraud/dispute data, not assumed from the spec.

## 6. Dispute resolution: the hardest line item to keep thin

Human-investigated disputes are expensive per case, and a marketplace at
any real volume will generate disputes constantly (wrong item, late
arrival, safety incident, a coalition member reneging). The main lever
this project actually has: the protocol's own structured audit
trail — signed mandates, offer/counter-offer history, commitment records,
fulfillment confirmations (`../design.md` §12) — should make most disputes
evidence-based and largely automatable (a claim can be checked against the
recorded state machine) rather than requiring a manual investigation from
scratch. This only works if implementations actually preserve and expose
that audit trail faithfully; a protocol that specifies the records but
whose implementations don't reliably retain/surface them loses this lever
entirely and falls back to expensive manual dispute handling.

## 7. Bottom line

≤2% all-in is **plausible, not guaranteed**, and specifically conditional
on:

1. Defaulting to low-cost real-time payment rails per region, treating
   card payment as an explicit costlier fallback (§3).
2. Keeping negotiation/matching logic computationally cheap by design —
   deterministic and rule-based, with LLM usage reserved for the
   human-facing layer only (§4) — the single most likely unforced way to
   blow the budget.
3. A reputation/trust system mature enough to keep fraud and dispute rates
   low, which is a function of accumulated volume and time, not something
   achievable at launch (§5).
4. A structured, faithfully-preserved audit trail that makes dispute
   resolution mostly automatable rather than a manual-investigation cost
   center (§6).

The honest expectation for an early pilot is a higher ratio than 2%,
converging toward it as the platform matures — this should be stated as
the target design converges toward, not advertised as day-one economics.
