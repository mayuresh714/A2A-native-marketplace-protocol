# Positioning, from first principles (revised — supersedes the ambiguous parts of `03`)

This doc exists because the positioning across `03-business-model-and-
customers.md` was genuinely unclear, and the confusion is worth naming
precisely before fixing it. `03` gestured at three different things at
once — "operate the neutral clearinghouse," "be Stripe for providers,"
and "sell one integration to LLM labs" — without ever saying which is the
company, who owns consumer distribution, or whether an incumbent like Uber
is a customer or a competitor. Those are three different businesses with
three different customers and three different moats. This doc strips the
idea to first principles and picks one.

## 1. The three questions, stated as asked

1. Is Uber going to buy this — do we sell into an incumbent's existing
   distribution?
2. Are we building our own distribution — our own marketplace/app?
3. Are we selling this infrastructure to giant LLM labs (OpenAI, Google)
   who already have billion-user distribution?

The reason all three feel plausible is that the current docs contain
sentences supporting each one. That's the bug. Only a first-principles
decomposition of the value chain resolves it.

## 2. First principles: decompose the value chain, ask who owns each layer

Strip the idea to the irreducible pieces of a single agent-mediated
service transaction, and ask, for each, **who realistically owns it and
whether we can or should.**

| Layer | What it is | Who realistically owns it | Can/should we own it? |
|---|---|---|---|
| **Consumer distribution** | The agent the end user actually talks to (their day-to-day assistant) | LLM labs (ChatGPT, Gemini) and OS vendors (Apple, Google) — this fight is being won *right now* and not by us | **No.** We have no right to win the consumer's primary assistant. Assume this is lost and design around it. |
| **Consumer intent → mandate** | Authorizing an agent to spend within bounds | AP2 (open standard, Google) | **No — reuse it.** Already open, already solving this. |
| **Negotiation / pooling / matching semantics** | The rules for how a demand-agent and supply-agents negotiate, pool, and commit | Nobody yet — this is the gap (`../design.md` §2) | **Author it, but as an *open protocol*, not a product** (see §4). |
| **Supply liquidity** | Onboarded, verified, matchable fragmented providers (drivers, plumbers, small operators) | **Nobody.** No one has given the long-tail provider an autonomous negotiating agent. This is the vacuum. | **Yes — this is the actual company.** |
| **Neutral clearing + anti-collusion + reputation/trust data** | The price-discovery mechanism, collusion monitoring, and accumulated reputation graph (`../design.md` §7, `../technical-deep-dive/04`) | Nobody neutral exists | **Yes — this is the moat** (§5). |
| **Payment rails** | Actually moving the money | UPI / cards / bank rails via AP2 (`../technical-deep-dive/07` §3) | **No — reuse per region.** |

Read the "can/should we own it" column top to bottom and the strategy
falls out mechanically: **we rent or open-source every layer except two —
supply liquidity, and neutral clearing/trust. Those two are the company.
Everything else we deliberately do not try to own.** The reason the
positioning felt unclear is that `03` never drew this line; it kept one
foot in "own the consumer relationship too" (posture ambiguity) and one
foot in "just be an open protocol" (own nothing).

## 3. Now answer the three questions directly

### Q1 — Is Uber a customer? No. Uber is an incumbent to route around, and in our best markets there is no Uber to sell to.

Uber's entire moat **is** being the closed graph that takes 25-30% by
sitting between rider and driver. An open protocol that lets a rider's own
assistant negotiate directly with a driver's agent is an *existential
disintermediation threat* to Uber, not a tool Uber buys. Uber has every
incentive to resist, not adopt.

But the sharper first-principles point: **in the verticals where this
protocol actually wins (`02-market-fit-framework.md` scored them —
intercity ride-sharing, home services, freight backhaul, event vendors),
there is no dominant Uber-equivalent to sell to in the first place.** That
fragmentation is *why* the protocol has room to work there
(`01-individual-vs-platform-competition.md` §2-3). "Does Uber buy this" is
a category error: the markets with an Uber to sell to are exactly the
markets this protocol shouldn't be fighting in (Uber's own on-demand
dispatch scores 0/8), and the markets this protocol should fight in have
no such incumbent. Uber becomes relevant only as a *late defensive
adopter* if an open agentic marketplace reaches enough scale to threaten
it — and by then we've already had to win without it.

### Q2 — Do we build our own distribution? Yes on supply, no on consumer. This is the whole asymmetry.

- **Consumer distribution: no** (per §2 — it's lost to the labs, don't
  fight it). Building a consumer app (posture (C) in `03`) is the worst
  option: enormous CAC, no edge on the thing consumers care about (a
  trusted booking flow incumbents already have), and it's a race we have
  no right to win.
- **Supply distribution: yes, emphatically** — and this is the part `03`
  had right but buried. Nobody is giving the fragmented long-tail provider
  an autonomous agent. Onboarding, verifying, and building trust data for
  millions of small providers is unglamorous, locally-textured, slow work
  that (a) the labs have no interest in doing, (b) incumbents do only
  inside their walled gardens, and (c) becomes a real asset precisely
  because it's hard. **Our "own distribution" is the supply network, not a
  consumer audience.**

### Q3 — Do we sell infrastructure to the LLM labs? No — we don't "sell infra" to them at all. They are a *distribution partner*, not a customer, and the reframe matters.

The trap in "sell our infrastructure to OpenAI/Google" is: if the protocol
is genuinely open, why would they buy anything? They'd just implement the
open protocol and talk to providers directly. Correct — and that's fine,
because **the protocol is not what has value. The supply liquidity and the
neutral clearing/trust layer are.** The labs integrate the *open protocol*
for free (no lock-in is exactly why they'll adopt it, the same reason they
adopted A2A) — and doing so gives their users the ability to actually
*book and negotiate real-world services*, which is strategically valuable
to the labs regardless of us. In exchange, their users reach **our
onboarded, verified supply**, cleared through **our neutral trust layer.**

They don't want to build the two layers we own, for concrete reasons:
- **Neutrality:** a clearinghouse owned by OpenAI is not neutral toward
  Google's agents, and providers won't trust one lab to set clearing
  prices or hold reputation across a market that includes that lab's
  rivals. Multi-homing *requires* a neutral operator — the same reason
  Visa is neutral across competing issuing banks.
- **Antitrust surface:** being the price-discovery and anti-collusion
  operator across thousands of independent competing merchants
  (`../design.md` §7) is a regulated-utility-shaped role a big lab has
  strong reasons *not* to want to own — it invites exactly the scrutiny
  they avoid.
- **It's not their business:** a thin B2B clearing fee is a rounding error
  to a lab monetizing intelligence and consumer subscriptions; onboarding
  long-tail plumbers is pure distraction. They'd rather integrate than
  build.

So the labs are the channel through which we *rent* consumer distribution
via an open protocol — not an entity we sell a product to. We don't invoice
OpenAI. We make their assistant more useful for free, and we monetize the
supply side of the transactions that flow as a result (§6).

## 4. Why the protocol must be open — and why that is not the same as "we have no business"

The single most important distinction the old docs missed: **the protocol
and the business are different things.**

- **The protocol is an open standard.** Like HTTP, like A2A and AP2
  themselves — you cannot sell it, and trying to monetize or close it
  guarantees it won't be adopted (someone forks the open version, or the
  labs simply don't touch a proprietary lock-in). Its job is *adoption and
  neutrality*, not revenue. We author and steward it — which positions us
  as the natural operator of the layers that do have value — but we do not
  own it.
- **The business is the operator of the two non-open layers** — supply
  liquidity and neutral clearing/trust. That's where money and moat live.

Conflating these is what made `03` read as incoherent: it kept trying to
find the business *in the protocol*. There is no business in the protocol.
The business is in the liquidity and the clearinghouse that the open
protocol makes possible.

## 5. The one-sentence positioning

> **We are the neutral supply-side network and clearing/trust layer for
> agent-mediated service commerce — the "Visa + exchange clearinghouse"
> for fragmented real-world services — sitting beneath an open negotiation
> protocol that lets any consumer's AI assistant reach our verified supply
> without anyone owning the whole graph.**

Unpacked against the closest analogies:

- **Like Visa/Mastercard** — a neutral network sitting between two sides
  neither of which we own (issuers/cardholders ↔ merchants; here
  labs/consumers ↔ providers), taking a thin toll, defensible by
  neutrality and ubiquity rather than by owning either endpoint.
- **Like a stock exchange + clearinghouse** — we run neutral price
  discovery and settlement (`../technical-deep-dive/04`), moated by trust,
  liquidity, and (eventually) regulatory standing, not by secrecy.
- **Like Stripe — but only for the onboarding wedge, not the core.** The
  Stripe analogy in `03` was over-extended: Stripe is a toll on top of
  existing card rails, it does not run neutral price discovery across
  competing merchants. We borrow Stripe's *provider-onboarding ease* as
  the cold-start wedge (§7), but the enduring business is the network +
  clearinghouse, which is more exchange-shaped than Stripe-shaped.
- **Explicitly NOT like Uber** — Uber owns the graph and both endpoints'
  relationships. Our entire thesis is that owning the graph is the thing
  to *avoid* (`../technical-deep-dive/05`). If we drift toward owning the
  consumer relationship or locking supply exclusively, we've become the
  thing we're routing around.

## 6. Who pays, precisely

Follow the payments analogy, because it resolves the "who's the customer"
question cleanly: **the fee comes out of the transaction, borne by the
supply side, the same way merchant interchange works.**

- The **consumer** pays nothing extra to us; their assistant is free to
  them (paid for by the lab's own subscription/business).
- The **LLM lab** pays us nothing — and we may even share a slice of the
  fee *back* to them as an incentive to route through our network rather
  than a rival's, exactly as card networks share interchange economics to
  steer routing. (Open question — see below.)
- The **provider** effectively pays the thin ≤2%-at-maturity fee
  (`../technical-deep-dive/07`), taken from the transaction they're
  receiving — and does so gladly because the alternative is a 25-30%
  incumbent take or manual self-marketing. This is the same structure as a
  merchant paying interchange: the side *receiving* the money pays the
  network fee.

This also cleanly separates us from the labs' own commerce ambitions
(OpenAI's ACP, `../design.md` §2): ACP/AP2 are *checkout* protocols for
buying a listed SKU from one merchant's catalog. We are the *negotiation
and pooling* layer for non-listed, dynamic, fragmented service supply, and
we can *settle* via AP2. We complement the labs' commerce stack rather than
competing with it — another reason they integrate rather than resist.

## 7. What this means for the cold-start wedge

Positioning fixed, the sequencing in `04-scaling-to-billions-gtm-
roadmap.md` still holds, but its logic is now clearer: we bootstrap the
**supply** layer first (the asset only we will build), using
provider-enablement tooling as the Stripe-like wedge, in one narrow
high-fit shard (`02-market-fit-framework.md`). Only once a shard has real
verified supply liquidity do we open the *open protocol* endpoint to
consumer-agent platforms — at which point their existing billion-user
distribution flows into our supply for free. The labs are a **Phase 3
distribution unlock**, not a Phase 0 customer to go sell to. Trying to sell
the labs first, before supply liquidity exists, is backwards — there's
nothing on the network worth their integration yet.

## 8. The honest downside of this positioning (stated, not hidden)

First-principles honesty cuts both ways, so the trade-off this positioning
accepts:

- **The neutral-clearinghouse position is defensible but thin-margin and
  slow.** Visa-like and exchange-like businesses are enormously valuable
  *at scale* but take years to reach it and win on trust/ubiquity, not on
  a flashy product. This is not a fast, winner-take-all land grab.
- **Neutrality and single-company value are in tension.** The more
  credibly neutral we must be to get the labs and competing providers to
  multi-home on us (§3), the more pressure there is for the clearinghouse
  to become a consortium or foundation — in which case a single company
  captures less of the value (`05-open-business-issues.md` and
  `../technical-deep-dive/05` §2 already flag this and it remains
  genuinely unresolved).
- **A well-funded competitor can run the same open protocol.** Openness
  cuts both ways: our protocol being open means someone with deeper
  pockets could stand up a competing neutral network on it. Our only
  durable defenses are being *first to real liquidity* and owning the
  *verified reputation graph* — which is exactly why §7's supply-first
  cold-start is not optional flavor, it's the whole defensibility play.

The positioning is therefore a deliberate bet: **occupy the one seat
(neutral supply + clearing) that is both necessary and one everyone else
would rather not sit in, accept that it's a slow trust-and-liquidity
business rather than a fast platform grab, and treat the open protocol as
the wedge that makes the labs bring their distribution to us for free** —
rather than fighting them, fighting Uber, or trying to own a consumer
audience we have no right to win.
