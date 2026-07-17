# Home services — electricians, plumbers, handymen, small local contractors

## 1. Why this fits the pattern

Same structural problem as intercity travel — many independent providers
(often one-person or few-person businesses), many consumers, perishable
capacity (a tradesperson's day has a fixed number of job-slots that expire
unused) — but with two differences that make it a harder, more realistic
test of the protocol than travel: **the job scope, and therefore the price,
usually isn't fully known until the provider inspects the problem**, and
**this is a stranger entering someone's home**, which raises the trust bar
above almost anything in the travel doc.

## 2. Today's pain

- **Consumer side:** a fuse keeps tripping, or a tap won't stop leaking.
  The person calls 3-4 numbers from a local directory or app, describes
  the problem repeatedly, gets quoted wildly different prices because
  everyone quotes blind, waits on multiple call-backs, and often just
  takes whoever answers first regardless of price or quality — urgency
  suppresses their own negotiating power.
- **Provider side:** a solo electrician loses paid time either being
  unreachable while mid-job (missed new leads) or context-switching to
  answer calls constantly. Off-peak hours or slow days have zero mechanism
  to advertise sudden availability to demand that exists *right now*
  somewhere nearby.

## 3. Actors / provider types

- **Consumer agent** — represents the homeowner/tenant.
- **Provider agent types:**
  - *Independent tradesperson* (one electrician, one plumber) — negotiates
    freely, scope/price often only firm after inspection.
  - *Small local firm* (3-10 person contracting business) — negotiates,
    but with dispatch across multiple staff, so an "offer" is really
    "we have someone free in this window."
  - *On-call/emergency service* — different urgency tier, different
    (higher) baseline pricing, less negotiation, mostly quote-and-accept.
- **Trust/Attestation service** — far more load-bearing here than in
  travel: license verification, insurance status, background-check
  status, past-job photos/ratings. A provider agent's "offer" is close to
  worthless to a consumer agent without a verifiable attestation attached.

## 4. Market structure

Two regimes coexist in the same market and the protocol has to support
both:

- **Emergency/urgent (same-day):** thin negotiation, thick urgency —
  consumer wants fastest qualified match, not best price; time-to-arrival
  matters more than a few percent on price.
- **Scheduled/non-urgent (this week, flexible):** real negotiation space —
  price, exact time window, whether parts are provider-supplied or
  consumer-supplied, are all points of back-and-forth.

Price is **provisional until inspection** in both regimes for anything
beyond the simplest jobs: an initial `Offer` is really a quote *range* plus
a call-out fee, with a final price renegotiated (or auto-confirmed within
a pre-authorized ceiling) once the provider is on-site and has actually
seen the problem.

## 5. Worked example

Consumer: kitchen tap won't stop dripping, wants it fixed today, budget
ceiling ₹1500 for a standard tap-washer job but open to more if it turns
out to be a valve replacement.

1. Consumer agent posts intent: "plumbing, leak/drip, today, ceiling ₹1500,
   escalate-to-₹3500-with-confirmation if scope expands," with location
   and a couple of photos of the tap attached (a plumbing-specific intent
   field the travel schema doesn't need).
2. Three independent plumber agents and one small firm's dispatch agent
   respond within minutes: two offer a same-day slot with a call-out fee
   + estimated range; one is booked solid and declines; the firm offers a
   slot with an attestation showing verified license + 4.8-star rating
   over 60 past jobs.
3. Consumer agent picks the firm's offer (rating + verified attestation
   outweighs a slightly lower quote from an unverified independent),
   confirms the call-out.
4. On-site, the plumber agent (or the plumber, via their agent) reports
   the actual issue is a worn valve, not just a washer — proposes a
   revised price of ₹2800, still under the ₹3500 escalation ceiling the
   consumer pre-authorized, so the provider agent's Commitment updates and
   the consumer's agent auto-confirms without waking the human up, per the
   mandate set in step 1.
5. Job done, payment settles via AP2 mandate, reputation feedback recorded
   on both sides (provider gets a rating; consumer's on-time-payment /
   accurate-problem-description history feeds their own reputation, which
   matters for step 2 above over time).

## 6. Coalition/pooling angle

Weaker than travel, but real on the **provider** side: a tradesperson's
agent, seeing three small jobs within a few streets of each other today,
can propose batching them into one efficient route (similar in spirit to
the freight/logistics backhaul problem, §6 of that doc) — quoting a small
discount to each consumer in exchange for a flexible time window, in
return for the provider not wasting travel time between jobs. This is a
**provider-side route-batching coalition**, not a consumer-side one — the
three homeowners never need to know about each other.

## 7. Price discovery / anti-cartel considerations

Local trade services are exactly the kind of fragmented, geographically
bounded market where informal price coordination already happens today
(a handful of electricians in a small town knowing roughly what everyone
charges) — the protocol shouldn't make that structurally easier by giving
every provider agent a live read on every competitor's current price.
Applying the main doc's reference-price-band approach (§7) here means:
publishing a *neighborhood-level* reference band for common job types
(standard tap repair, socket replacement) sourced from historical cleared
prices, without exposing any individual competitor's live quote to others
— the band should come from aggregate history, not real-time
cross-visibility between provider agents in the same neighborhood.

## 8. Trust, safety & compliance caveats

- **This is the highest physical-trust vertical in this folder** — a
  stranger enters a home, often when a resident is alone. License,
  insurance, and identity verification aren't optional nice-to-haves the
  way "verified vehicle" was a soft signal in travel — they should gate
  whether a provider agent's offers are shown at all.
  - Verify from an authoritative source, not a self-declared field — a
    plumber saying they're licensed is not the same as an attestation
    service checking a license registry.
- **Liability for scope changes.** A price renegotiation mid-job (step 4)
  needs the same non-repudiable audit trail as any commitment change —
  "the provider claimed a valve was worn" is exactly the kind of claim
  that generates real-world disputes if unrecorded.
- **Emergency-tier abuse risk.** A provider agent could mis-classify a
  routine job as "emergency" to justify a higher, less-negotiated price;
  the protocol needs an objective definition of urgency tiers, not a
  self-declared one a provider agent controls unilaterally.

## 9. Why this could be high impact

Extremely high-frequency, high-annoyance-per-transaction category — nearly
every household hits this multiple times a year, the search cost (multiple
calls, inconsistent quotes, no-shows) is one of the most-complained-about
parts of home ownership/renting, and the fragmented, hyper-local supply
side (millions of one-person businesses, no dominant platform in most
markets) means there's no incumbent single company positioned to solve it
centrally the way Uber solved city cabs — which is exactly the shape of
market this decentralized protocol is meant for.
