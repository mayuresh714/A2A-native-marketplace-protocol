# Event services — weddings and events, multi-vendor bundling

## 1. Why this fits the pattern

Every other doc in this folder has one consumer buying one kind of
service. An event (a wedding, a birthday, a corporate offsite) is the
opposite: **one consumer needs several different provider types —
caterer, photographer, decorator, venue, sometimes a band/DJ — to all
independently agree to the same date, and to price/scope in a way that
works as a bundle**, not each negotiated in isolation. This is the doc
that tests **supply-side coalition formation** as a first-class case
rather than an edge case — the mirror image of the travel doc's
consumer-side coalition (main doc §5).

## 2. Today's pain

- **Consumer side:** planning even a modest event means separately
  contacting a caterer, a photographer, a decorator, and a venue, each
  with their own availability, each quoting independently with no
  awareness of the others, and the consumer manually reconciling whether
  all four can actually do the same date, then re-negotiating with
  whichever one is the scheduling bottleneck. A full wedding planner
  service exists precisely because this coordination is hard enough that
  a specialized human profession does it — a strong signal this is a real
  coordination cost, not a minor annoyance.
- **Provider side:** each vendor (caterer, photographer, etc.) manages
  their own calendar in isolation and has no visibility into whether
  their open date is actually useful to anyone until a consumer happens
  to ask — a caterer with a free Saturday has no way to signal that
  usefully to a photographer who also has that Saturday free, even though
  matching the two would help both find the same client.

## 3. Actors / provider types

- **Consumer agent** — represents the person planning the event (date
  window, guest count, budget envelope — often a single total budget that
  needs to be *allocated* across vendor categories, which is a new
  requirement none of the other docs in this folder have).
- **Provider agent types**, several genuinely different categories
  competing/cooperating in the same negotiation:
  - *Venue* — usually the anchor constraint (fixes the date once booked);
    negotiates date, capacity, inclusions.
  - *Caterer* — negotiates per-head price, menu, sometimes tied to venue
    kitchen constraints.
  - *Photographer/videographer* — negotiates hours covered, package tier.
  - *Decorator* — negotiates scope/theme/budget tier.
  - *Entertainment (band/DJ)* — negotiates set length, timing around the
    other vendors' schedules (can't play during the caterer's service
    window, for instance).
- **Vendor coalition** — an ephemeral, opt-in grouping of *provider*
  agents (not consumer agents) that pre-coordinate into one bundled
  package for a single consumer's event — the structural mirror of the
  main doc's consumer coalition.

## 4. Market structure

Fully negotiable on both price and scope for every vendor category, but
with a **hard sequencing dependency** none of the other docs have: the
venue and date are usually load-bearing constraints that every other
vendor's availability must be checked against, not five independent
parallel negotiations. Budget allocation across categories is also
often more like one consumer-side pool split across vendors than five
separate budgets.

## 5. Worked example — this is the supply-side coalition case directly

A consumer wants to hold an event for ~80 guests on a Saturday in a
6-week window, total budget ₹5,00,000 across venue, catering, photography,
and decor, no fixed idea of exact split.

1. Consumer agent posts intent: guest count, date window, total budget,
   soft priority ranking across categories (e.g., "catering quality
   matters most, decor least").
2. Rather than the consumer agent separately shopping four categories
   (which is what today's manual process amounts to), it queries the
   registry for **existing vendor coalitions** that already coordinate
   with each other for this guest-count tier and date window — some
   caterers, photographers, and decorators in a given city already
   discover each other proactively (opt-in, ongoing, unlike the
   one-shot ephemeral consumer coalitions elsewhere in this project) and
   pre-form loose "we work well together and coordinate calendars" groups
   precisely because they've learned bundling wins more business than
   competing solo.
3. One such coalition — a venue, a caterer, and a photographer who
   already have a track record of matching availability with each other —
   responds with a **single joint offer**: one date, one combined price
   under budget, each vendor's portion itemized.
4. Consumer agent compares this bundle against assembling four separate
   solo vendors itself (checking each one's independent availability for
   the same date) — the coalition offer clears faster (one negotiation
   instead of four sequential ones) and, because the vendors already
   coordinate, has a much lower chance of a late scheduling conflict
   (a common real-world failure mode: booking a photographer only to
   discover the venue's hours don't match).
5. Consumer confirms; decor is still sourced separately since the
   coalition didn't include a decorator this time — the protocol needs to
   support a **partial-coalition-plus-independent-vendor** commitment, not
   assume either "one full bundle" or "fully separate" as the only shapes.

## 6. Coalition/pooling angle

The featured case for this doc, and structurally different from every
other coalition example in this project:

- **Standing, not ephemeral**, unlike the travel/food consumer coalitions
  — vendors that work well together have an incentive to keep
  pre-coordinating across many future events, not just one negotiation.
- **Supply-side, not demand-side** — providers bundling to win one
  consumer, not consumers pooling to unlock one provider.
- **Partial bundles are the common case**, not the exception — the
  protocol needs bundle-offers to compose with independently-booked
  vendors cleanly (§5, step 5), rather than assuming an all-or-nothing
  package.

## 7. Price discovery / anti-cartel considerations

Standing vendor coalitions are exactly the structure that could tip from
"legitimate efficient bundling" into **anti-competitive steering** — a
group of venues/caterers/photographers who habitually bundle together
could use that coordination to quietly exclude a lower-priced independent
competitor from ever being considered, or to jointly hold pricing above
what solo competition would produce, which is a *different* failure mode
from the pure price-collusion risk in the main doc (this is
coalition-as-exclusion, not coalition-as-price-fixing). Mitigations:
consumer agents should always be shown independent solo-vendor options
alongside any standing-coalition bundle offer, never only the bundle, so
a coalition has to actually out-compete unbundled alternatives on
merit — the protocol should make it structurally impossible for a
"convenient bundle" recommendation to quietly suppress solo competitors
from even being queried.

## 8. Trust, safety & compliance caveats

- **Standing coalitions need transparency about what they are.** A
  consumer should be able to see "these three vendors habitually work
  together" rather than mistaking a pre-coordinated bundle for an
  independently-assembled best-of-breed selection — non-obvious
  affiliation between nominally separate businesses is a disclosure issue
  in several consumer-protection frameworks, not just a nice-to-have.
- **Budget-allocation disputes.** When a consumer sets one total budget
  and a bundle allocates it across vendors, a later dispute (e.g.,
  photographer under-delivers) needs a clear record of what each vendor
  in the bundle was actually committed to and paid for, not just the one
  headline bundle price.
- **Sequencing/dependency failures.** If one vendor in a confirmed bundle
  cancels (a caterer drops out after the venue is already locked), the
  protocol needs a defined re-negotiation path for the remaining bundle
  members and the consumer, not just a generic cancellation.

## 9. Why this could be high impact

Event planning coordination cost is large enough to have spawned an
entire human profession (wedding/event planners) purely to solve the
cross-vendor scheduling problem described in §2 — a strong revealed-demand
signal that this coordination pain is real and people already pay to have
it solved by a human intermediary. An open protocol that lets
independent, unaffiliated vendors interoperate and (optionally)
pre-coordinate into standing bundles offers a lower-cost, more
transparent alternative to both "hire a planner" and "coordinate five
vendors yourself," without requiring any single platform to own the
entire vendor relationship the way a single events marketplace app would.
