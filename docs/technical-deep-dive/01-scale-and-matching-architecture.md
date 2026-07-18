# Scale and matching architecture

## 1. The naive problem

M provider agents, N consumer agents, all wanting to be matched against
each other for the same rough time/place window. Naive matching — every
consumer intent evaluated against every provider offer — is O(M×N) per
matching window. That's not a theoretical concern; it breaks fast:

- A single mid-size city on a Friday evening: ~5,000 concurrently active
  provider agents (drivers, vans, buses) and ~50,000 open consumer
  intents in the preceding hour → 250 million pairwise evaluations, before
  a single negotiation message is sent, and before coalition-formation
  (main design doc §5) adds a second combinatorial layer on top.
- This has to re-run continuously, not once — offers and intents expire,
  new ones arrive every second, and holds (§4 below) change availability
  mid-window.

So the real design problem is: **how do you avoid ever computing the full
M×N matrix**, while still finding the matches that are actually good.

## 2. Candidate generation before negotiation

Negotiation (the expensive, multi-round, agent-to-agent part) should only
ever run on a small, pre-filtered candidate set — never on the full
population. This mirrors exactly how real-time ad exchanges solve an
equivalent problem (millions of bidders, millions of ad impressions,
sub-100ms matching): index aggressively, filter cheaply, only do the
expensive per-candidate evaluation on a shortlist.

**Sharding by (corridor, time-bucket).** Route requests and provider
offers are keyed into a coarse grid: a corridor identifier (could be as
simple as an origin-region/destination-region pair, or a set of geohash/H3
hex-cell pairs for the endpoints) crossed with a time bucket (e.g.,
15-minute windows). Matching only ever happens *within* a shard. This is
the same idea as sharding a stock exchange's order book by symbol — each
shard is independently and cheaply matchable, and shards scale
horizontally with zero cross-shard coordination needed for the common
case.

**Within a shard, index further.** Even within one (corridor, time-bucket)
shard, don't brute-force compare every intent to every offer — maintain
inverted indexes on the filterable fields that actually gate a match
(minimum seats available, max price, provider type, verified-attestation
required, comfort-preference flags) so a consumer intent's candidate offers
come back as an indexed lookup, not a scan. Same pattern as ad-exchange
real-time bidding (OpenRTB-style) candidate generation, and the same
pattern used by e-commerce/search recall-then-rank pipelines generally:
cheap filtering to a shortlist, expensive evaluation only on the
shortlist.

**Bound the fan-out.** A consumer intent should never broadcast to every
provider agent in its shard, even post-filtering. Cap to top-K candidates
(e.g., K=20) ranked by a cheap scoring heuristic (price fit, historical
acceptance-rate, reputation) before any negotiation messages are sent.
This bounds per-intent message complexity to O(K), and total system
message complexity to O(N×K) instead of O(N×M) — the difference between a
tractable and an intractable system as M and N both grow.

## 3. Preventing double-booking under concurrency

Perishable capacity (a seat, a table, a time slot) creates the classic
inventory-oversell problem: many consumer agents can be negotiating
against the same provider offer simultaneously, and more than one might
try to commit to the last seat at the same moment. This is not a new
problem — it's the same one flight booking, e-commerce flash sales, and
event ticketing all solve — and the same solution applies:

- **Single authoritative owner per capacity unit.** Each unit of capacity
  (this driver's this seat, this table's this time slot) has exactly one
  authoritative writer — the provider agent (or its registry shard, acting
  on the provider's behalf) — never a distributed consensus across
  organizations. This sidesteps needing cross-company distributed
  consensus entirely: you only need local concurrency control at the one
  place capacity is actually owned.
- **Optimistic concurrency control (OCC).** Every hold/commit operation
  carries a version number; a commit attempt against a stale version is
  rejected and the requester is told to re-fetch and retry against current
  availability, rather than using heavyweight locking that would stall
  every other consumer agent trying to check the same offer.
- **Short-lived hold tokens with explicit expiry** (already in the base
  schema — `hold_expires_at`) so a consumer agent that goes silent
  mid-negotiation doesn't permanently lock capacity away from everyone
  else; expiry is enforced by the provider-side owner, not trusted to the
  requester.

## 4. Handling load spikes (thundering herd)

Popular corridors at predictable peak times (Friday evening exodus from a
city, a festival weekend) will spike far above average load on specific
shards. Two standard mitigations apply directly:

- **Queue-based fan-out instead of synchronous broadcast.** A burst of
  consumer intents hitting one shard should enqueue rather than
  synchronously trigger negotiation with every candidate provider at once;
  provider agents (especially small, individually-run ones) shouldn't be
  hit with a burst of simultaneous negotiation requests they can't process.
- **Shard-local backpressure**, not a global rate limit — a spike on one
  corridor shouldn't degrade matching quality on unrelated shards, which
  is exactly why sharding by (corridor, time-bucket) rather than running
  one global matcher matters operationally, not just algorithmically.

## 5. Cross-shard cases (the exception, not the default)

Most matching is shard-local by construction. Two situations break that:

- **Coalition formation near a shard boundary** (main doc §5's Pune
  example: one shard for "Pune-Satara, 15:00-17:00" and an adjacent one
  for "Pune-Vadgaon, 15:00-17:00" might need to see each other to form a
  joint offer with a provider whose route spans both). Handle with
  overlapping shard membership for coalition-discovery specifically
  (an intent can register into more than one adjacent shard's
  coalition-discovery pool) rather than redesigning the base matching
  shards around it.
- **Fixed-schedule providers** (bus corporations, railway) that span many
  corridors/time-buckets at once — these don't need dynamic matching at
  all (§4 of the main design doc — they're quote-and-book, not negotiated),
  so they're better modeled as a directly queryable schedule index a
  consumer agent checks in parallel with dynamic-shard matching, not
  forced through the same negotiation-oriented sharding.

## 6. Target numbers (illustrative, to be validated against a real pilot)

- Candidate-generation latency: sub-100ms per intent (matches ad-exchange
  RTB precedent — this step has to be index-lookup-fast, not
  negotiation-slow).
- Negotiation round latency: seconds, not milliseconds — this is agent
  reasoning and possibly human-confirmation latency, fundamentally
  different from the candidate-generation step above; the two should be
  architected as separate stages with very different latency budgets, not
  one undifferentiated pipeline.
- Shard sizing: keep each (corridor, time-bucket) shard's active
  population in the low thousands at most — if a shard is consistently
  overloaded, split the time-bucket finer or the corridor geography finer,
  the same way an exchange splits an oversubscribed order book.
