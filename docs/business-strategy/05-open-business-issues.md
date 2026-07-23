# Open business issues (catalog, not resolved)

A consolidated list of business questions raised across this folder and
the rest of the repo that genuinely don't have answers yet — flagged
explicitly rather than glossed over, so they get revisited deliberately
instead of being silently assumed away as the project moves forward.

## Governance

- **Who governs `ServiceCategory` registration and the neutral
  clearing/attestation operator role**
  (`../technical-deep-dive/05-moat-and-strategy.md` §1c,
  `../core-model/03-extensibility-and-vertical-mapping.md` §3)? A single
  company, a multi-party consortium, a foundation? This decision shapes
  whether the "neutral utility" positioning is credible at all — a
  single for-profit company claiming neutrality over the price-clearing
  mechanism that determines its own revenue is a real conflict of
  interest that has to be structurally addressed, not asserted away.
- **Who can veto or override a `ServiceCategory`'s safety-critical
  defaults** (e.g., home-healthcare's refusal to allow auto-commit,
  `../industries/home-healthcare.md` §6-8)? If the governing body is
  also commercially incentivized to relax friction for growth, this is a
  direct conflict.

## Competitive/strategic

- **Incumbent-copy risk.** If any single vertical shows real traction, an
  incumbent (BlaBlaCar, a regional fleet aggregator, an event-vendor SaaS
  platform) could copy the negotiation/pooling idea *inside their own
  closed platform*, capturing the value this project demonstrated without
  ever adopting the open protocol — "embrace and extend" is a standard
  incumbent response to an open challenger proving out a new mechanism.
  Not addressed anywhere yet; possible mitigations (moving fast on
  network effects, leaning on portable-reputation as a switching cost)
  are untested.
- **The moat tension itself is unresolved, not just described.**
  `../technical-deep-dive/05-moat-and-strategy.md` recommends the neutral-
  utility position but doesn't resolve how that stays viable if a
  well-funded competitor decides to run the same open protocol as a
  loss-leader to capture liquidity — an open protocol can be run by more
  than one operator, including one with much deeper pockets.

## Regulatory/legal

- **Regulatory classification of the operating entity, per jurisdiction.**
  Is a company operating the registry/clearing layer a money transmitter,
  a marketplace facilitator, a payments processor, or none of the above
  since (per the AP2-mandate design) it may never directly custody funds?
  This varies by country and isn't resolved for any of the target
  verticals yet.
- **Liability insurance for autonomous-agent commitments doesn't exist as
  a product yet** (`../technical-deep-dive/06-caveats-and-practical-
  realities.md` §2). Early pilots likely proceed genuinely uninsured
  against this specific risk class, which is a real, unquantified
  business exposure, not just a legal footnote.

## Adoption / bootstrapping economics

- **Who subsidizes the first transactions in a new shard** before real
  liquidity exists (`04-scaling-to-billions-gtm-roadmap.md` §1)? Every
  two-sided marketplace bootstrap has historically required some form of
  subsidized supply or demand generation in its earliest days — this
  project hasn't decided whether/how it funds that, or whether it expects
  organic bootstrapping to work without it (risky, per the same section's
  liquidity-floor argument).
- **Provider trust in delegating pricing authority to software.** Would a
  small independent driver or plumber actually authorize an agent to
  negotiate price on their behalf, unsupervised, within a mandate ceiling?
  This is an adoption-psychology question, not a tooling question — the
  mandate/autonomy design (`../core-model/01-entities.md` §8) assumes
  providers will grant this once trust is established, but that trust
  threshold hasn't been tested with real small-business owners.
- **Consumer trust equivalent, at a different ceiling.** Will end users
  authorize an agent to commit real money on their behalf beyond a small,
  low-stakes ceiling — and does that ceiling rise fast enough for the
  higher-value verticals (freight, events) to ever reach meaningful
  autonomy, or does trust-building have its own slow adoption curve
  independent of the technology being ready?

## Market-choice risk

- **Choosing the first pilot market is itself a bet with real downside.**
  `02-market-fit-framework.md` narrows the field, but picking the *specific*
  first corridor/city/vertical inside that shortlist is a real strategic
  decision this repo hasn't made — a wrong first choice (one that turns
  out to have a hidden regulatory blocker, or weaker latent demand than
  assumed) costs the scarce early credibility this project needs to reach
  Phase 1 at all (`04-scaling-to-billions-gtm-roadmap.md`).

## Brand/IP

- **How an open-protocol business protects any commercial position at all
  without contradicting its own openness claim** — trademark on the
  reference implementation's name, a certification mark for compliant
  implementations, or nothing? This is unresolved and directly follows
  from the moat tension above; it hasn't been decided, only flagged.

---

None of the above blocks continuing design work in the rest of this repo
— but none of them should be assumed solved either. Revisit this list
before committing real capital or a public pilot announcement, since
several of these (first-market choice, subsidized bootstrapping, insurance
exposure) are the kind of thing that's much cheaper to get wrong on paper
than in a live market.
