# Supply/demand imbalance: what the network does, and what it must never do

Two distinct failure modes, and — per the design notes — they must be
handled by *opposite* mechanisms. Getting this asymmetry right is a
direct extension of P1's anti-cartel stance, not a separate concern.

## 1. The two imbalance directions

- **Undersupply**: a partition has more demand than the locally available
  supply can serve (a corridor at peak hours, a skill category with too
  few verified providers).
- **Oversupply**: a partition has more supply than real demand can absorb
  (too many providers chasing too few requests in a category).

These are not symmetric problems and the notes are explicit that they
must not be solved the same way.

## 2. Undersupply → pull in supply from elsewhere (federation)

When a partition is structurally short of supply, the correct network-
layer response is to **widen the pool**, not to change matching rules
locally. This is exactly what
[`../platform-architecture/03-federation-and-interoperability.md`](../platform-architecture/03-federation-and-interoperability.md)
already designed: a network short on supply for a category/region can
discover and pull in supply from a **peered network** through the
DNS-like cross-network discovery layer and settle across networks through
the interbank-style settlement layer described there. Undersupply is a
liquidity problem, and federation is the network-layer mechanism built
specifically to solve liquidity problems that a single network can't solve
alone.

This also gives P12's "a joint offer can create new suppliers" a second
reading: within one network, a pooled demand signal can induce a *local*
provider to post new capacity (§`01` P12); at the inter-network level, the
same undersupply signal is what a federated peer network responds to by
routing its own supply in. Same underlying idea — a strong enough demand
signal recruits supply — expressed at two different scopes.

## 3. Oversupply → never manipulate demand; redirect supply instead

**The rule, stated as directly as the notes state it: a network must never
respond to oversupply by getting providers to coordinate and pressure or
persuade customers into buying more.** That is not a matching
inefficiency to solve — it is demand manipulation by a coordinated
supply-side bloc, which is structurally identical to what P1 already
forbids (`01-principles-and-lifecycle.md` §P1): providers acting together
to change outcomes on the demand side. Oversupply does not create an
exception to P1; it's the same prohibition seen from a different trigger.

**What the network does instead — two network-layer mechanisms, neither
of which touches the demand side:**

- **(a) Governance-controlled supply growth throttling.** A category's
  onboarding/activation of new supply is gated against real, observed
  demand for that category/partition — not against how many providers
  *want* to join. This is a Layer C (governance) function
  (`02-layers-governance-security.md`): the category's safety/health
  floor includes a supply-to-demand ratio ceiling, so a specialized
  category is structurally prevented from growing supply "out of
  proportion to demand," in the notes' own words, in the first place.
  Prevention beats correction — the same structural-over-detection
  preference already established for fraud (`02` Layer D).
- **(b) Redirect excess capacity via good alternatives, never coercion.**
  Where oversupply already exists, the network's job is to make the
  *provider's* next-best option genuinely good: surface adjacent
  categories or partitions with real unmet demand (including, per §2, a
  federated peer network that happens to be undersupplied in exactly this
  provider's category), and let the provider's own agent decide whether to
  redirect there. This is an **offer of a better option to supply**, not
  pressure applied to demand — the distinction is the entire point. A
  provider agent is free to decline and simply see less matching volume
  in an oversupplied category; nothing in the network compensates for
  that by pushing harder on consumers.

## 4. Why this belongs at the network layer, not as operator policy

An individual operator, left to their own incentives, might be tempted to
juice a struggling category's fill rate by nudging demand (surge-adjacent
tricks, artificial urgency, biased ranking that favors whichever provider
most needs volume). Making "never manipulate demand to clear oversupply"
a **network-layer rule** — not a per-operator policy choice — closes that
option off structurally for every operator on the protocol, the same way
P1 closes off provider price-fixing structurally rather than leaving it
to each operator's discretion. Layer C governance (`02`) is where the
supply-growth throttling and cross-network redirection mechanisms are
enforced; no operator implementation is conformant if it routes around
this rule by finding a demand-side lever instead.

## 5. Summary

| Imbalance | Forbidden response | Required response |
|---|---|---|
| Undersupply | — | Federation: pull supply from a peered network (§2) |
| Oversupply | Coordinated supply-side pressure/persuasion on demand (extension of P1) | Governance-throttled supply growth + redirecting excess capacity to real demand elsewhere, including federated peers (§3) |
