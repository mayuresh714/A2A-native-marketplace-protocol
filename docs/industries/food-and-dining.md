# Food & dining — restaurant table booking and food ordering

## 1. Why this fits the pattern

Two sub-markets, both fitting the perishable-capacity pattern, but the
"unit" being perishable is different from travel: it's a **time-slot**
(a table for two at 8pm; a kitchen's ticket-printer bandwidth in the next
20 minutes), not a vehicle seat. This tests whether the protocol's
hold-with-expiry and negotiation machinery generalizes past "moving people
between two points."

## 2. Today's pain

- **Table booking:** the popular restaurant is fully booked on the app for
  8pm, but a table might genuinely free up from a cancellation, or the
  restaurant would gladly seat a party of 2 at a 2-top at 8:15 instead of
  8:00 if anyone asked — humans don't call and ask, they just try a
  different restaurant, and the restaurant loses a seating it could have
  filled.
- **Food ordering:** a consumer wants a specific dish or dietary profile
  (say, high-protein, no dairy) *right now*; the current model is browse
  N restaurant menus and self-filter, not tell one agent your constraints
  and let it check what's actually kitchen-feasible in the next 30 minutes
  across many restaurants.
- **Restaurant side:** during a lull, a kitchen has spare capacity it has
  no live way to advertise beyond a generic app discount; during a rush,
  it has no way to signal "no new orders for 25 minutes" other than the
  app queue silently getting slower.

## 3. Actors / provider types

- **Consumer agent** — represents the diner (party size, time window,
  cuisine/dietary constraints, budget).
- **Provider agent types:**
  - *Restaurant table-booking agent* — negotiates seating time/party size,
    holds a table with expiry.
  - *Restaurant kitchen/order agent* — negotiates menu availability,
    substitutions, prep-time-based ETA, not seating.
  - *Delivery-fulfillment agent* (may be the restaurant's own rider network
    or a third-party aggregator's agent) — negotiates delivery ETA and fee,
    a distinct capacity pool from the kitchen's.
- These three are often three different companies today (restaurant,
  reservation platform, delivery platform) — the protocol lets them
  interoperate as separate agents instead of requiring one company to own
  the whole stack, which is a real structural difference from how
  OpenTable/Zomato/delivery apps currently bundle all three.

## 4. Market structure

- **Table booking** is genuinely negotiable: time, party size, and table
  location (window vs. back) are all soft, and a restaurant's agent can
  counter-offer a slightly different time the way a driver counter-offers
  a slightly different departure.
- **Food ordering** is closer to fixed-catalog (ACP-style, per the main
  doc's prior-art table) most of the time — but becomes genuinely
  negotiable at the margins: substitutions, prep-time trade-offs ("15 min
  faster if you drop the side"), and bulk/group orders (below).

## 5. Worked example

A group of 5 wants dinner at 8pm at a specific popular restaurant; the
app shows fully booked.

1. Consumer agent posts intent: party of 5, 7:30-8:30pm window, this
   restaurant preferred but two similar-cuisine alternates acceptable.
2. Restaurant's table-booking agent checks live floor state (not just the
   static booking calendar): a 6-top is currently occupied by a party of 4
   expected to leave by 8:10. It counter-offers 8:15 instead of 8:00,
   holds it provisionally.
3. Consumer agent's mandate allows up to 20 minutes of wait flexibility
   without asking the human — it auto-accepts the 8:15 hold.
4. In parallel, one member of the party has a dairy allergy; the
   restaurant's kitchen/order agent (queried at booking time, not
   discovered awkwardly at the table) confirms a substitutable dish exists
   and reserves it against the ticket queue for that slot.
5. Table confirms at 8:10 when the earlier party actually leaves;
   consumer agent notifies the human with the confirmed time; no further
   human action needed.

A second, food-ordering example shows the pooling angle directly (§6).

## 6. Coalition/pooling angle

This is the one vertical in this folder with a clean **consumer-side
pooling** example as direct as the travel one: several nearby individual
food orders below a restaurant's minimum-order-for-free-delivery threshold
can have their consumer agents discover each other (opt-in, same
apartment complex/office building, overlapping delivery window), merge
into one **combined order** that clears the free-delivery minimum and
lets one rider fulfill all of them in one trip — directly mirroring the
Pune-Kolhapur consumer coalition (main doc §5), just with a delivery
batch instead of a vehicle seat. Compatibility matching (main doc §6) is
close to irrelevant here since coalition members never physically meet;
the only real per-member checks are dietary/payment-share consent.

## 7. Price discovery / anti-cartel considerations

Lower risk than travel or freight for outright collusion (restaurants
mostly compete on menu/brand, not on a single fungible "route"), but two
narrower risks matter:

- **Delivery-fee cartelization** across nominally competing
  delivery-fulfillment agents in the same zone during high-demand windows
  (dinner rush) is structurally the same risk as the travel doc's surge
  scenario, and should use the same reference-band-plus-monitoring
  approach for delivery fees specifically, not menu prices.
- **Table-booking scarcity abuse** — a popular restaurant's agent
  quietly reserving "reveal a table exists" for higher-paying negotiation
  paths is a soft version of gouging; a visible baseline (this restaurant's
  usual availability pattern) helps consumer agents tell a genuine sellout
  from an artificially gated one.

## 8. Trust, safety & compliance caveats

- **Allergy/dietary correctness is a safety issue, not a preference one.**
  A misreported "yes, dairy-free" from a kitchen/order agent that turns
  out wrong is a health incident, not a bad experience — this needs a
  higher-confidence attestation (verified ingredient data, not a
  self-declared kitchen claim) than most other fields in this doc.
- **Group-order payment splitting** in the pooling case (§6) needs its own
  mandate structure — each participant authorizes only their own share,
  and the merge shouldn't create a situation where one person's agent can
  accidentally commit another's payment.
- **Delivery-fulfillment liability** (late/cold/wrong food) sits between
  the restaurant and the delivery agent; the protocol needs a clear
  fulfillment-confirmation record showing which of the two agents held
  responsibility at each stage, for dispute resolution.

## 9. Why this could be high impact

Among the highest-frequency transaction categories that exist (multiple
times a week for many consumers), and the current three-way split between
restaurant/reservation-platform/delivery-platform is exactly the kind of
multi-company fragmentation an open agent protocol is suited to bridge —
today that fragmentation is hidden behind one dominant app's UI per
category; an open protocol lets a consumer's single agent reason across
all three without any one platform needing to acquire the others.
