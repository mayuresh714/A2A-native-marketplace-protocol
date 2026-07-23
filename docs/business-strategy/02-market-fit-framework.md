# Where this fits: a scoring framework

`01-individual-vs-platform-competition.md` worked through two examples by
hand. This turns that reasoning into a repeatable rubric, so the next
market someone proposes ("what about X") can be scored instead of argued
about from scratch.

## 1. The four dimensions

| Dimension | 0 (poor fit) | 1 (moderate fit) | 2 (strong fit) |
|---|---|---|---|
| **Negotiation surface** | Fixed price/schedule, nothing to negotiate (a movie seat, a train ticket) | Some flexibility (delivery ETA, minor substitutions) | Price, time, and scope all genuinely negotiable (a driver's route, a plumber's quote) |
| **Supply fragmentation** | One or few dominant, already-integrated suppliers | Moderately fragmented, some consolidation | Many small, independent, mutually-unknown providers — no one owns the graph |
| **Existing-platform efficiency** | A platform already matches this well and cheaply (low friction today) | A platform exists but still has real friction (manual accept/reject, poor fill rates) | No platform has solved this well; humans still do most of the matching manually |
| **Assistant-integration headroom** | A dominant incumbent is already wired directly into major consumer AI assistants (bespoke deal, like Uber×OpenAI) | Partial/regional integration exists | No incumbent has locked in assistant-platform distribution yet — genuinely open lane |

Score each market 0-2 per dimension, sum out of 8. This isn't meant to be
precise to the point — it's meant to make the "is this our fight"
judgment call from `01-individual-vs-platform-competition.md` repeatable
and falsifiable rather than vibes-based.

## 2. Scored examples

| Market | Negotiation surface | Supply fragmentation | Existing-platform efficiency (inverted: high friction = high score) | Assistant-integration headroom | Total | Verdict |
|---|---|---|---|---|---|---|
| Uber-style on-demand city rides | 0 | 0 (Uber dominant) | 0 (already efficient) | 0 (Uber×OpenAI already live) | **0/8** | Avoid — this is the wrong fight, per `01-individual-vs-platform-competition.md` §2 |
| BookMyShow-style fixed-inventory ticketing | 0 | 1 | 1 | 1 | **3/8** | Weak fit — no negotiation surface to recover; a distribution problem, not a matching one |
| Intercity ride-sharing (`../design.md`) | 2 | 2 | 2 (BlaBlaCar still manual swipe/accept) | 2 (no incumbent locked in yet) | **8/8** | Strong fit — the project's own starting vertical, and it scores at the ceiling for a reason |
| Home services (`../industries/home-services.md`) | 2 | 2 (millions of one-person businesses) | 2 | 2 | **8/8** | Strong fit |
| Freight backhaul matching (`../industries/freight-logistics.md`) | 2 | 2 | 1 (Uber Freight/Convoy already tried, imperfectly) | 2 | **7/8** | Strong fit, with real prior-art to benchmark against |
| Event vendor bundling (`../industries/event-services.md`) | 2 | 2 | 2 (a whole human profession exists to solve this manually) | 2 | **8/8** | Strong fit |
| Restaurant table booking (`../industries/food-and-dining.md`) | 1 | 1 (OpenTable/Zomato-style platforms already fairly liquid in many markets) | 1 | 1 | **4/8** | Moderate — real value in the group-order/pooling angle specifically, weaker on the booking side alone |
| Home healthcare visits (`../industries/home-healthcare.md`) | 1 (price often payer-fixed) | 2 | 2 | 2 | **7/8** | Strong fit on matching, but `../industries/home-healthcare.md` §6-8 already flag this as the vertical needing the most caution before pursuing it commercially |
| Generic e-commerce checkout (fixed-catalog retail) | 0 | 0-1 | 0-1 | 0 (ACP/UCP already contesting this exact space, `../design.md` §2) | **0-2/8** | Avoid — already being fought over by ACP/UCP; not this project's differentiated ground |

## 3. Reading the table

- **High scores cluster exactly on the verticals `../industries/` already
  chose** — not a coincidence; those were picked in the first place
  because they stress-tested different facets of a market this protocol
  actually fits (`../industries/README.md`'s own selection criteria).
  This table is a retroactive check that the selection was sound, not
  just a restatement of it.
- **The two examples the user raised land at opposite ends** — Uber
  scores 0/8 (avoid), and BookMyShow scores 3/8 (weak, avoid as primary
  target) — which confirms `01-individual-vs-platform-competition.md`'s
  conclusion quantitatively rather than just narratively.
- **A score isn't a guarantee** — freight scores 7/8 but carries the
  highest collusion risk of any vertical covered
  (`../technical-deep-dive/07`... rather, `../design.md` §7 and
  `../industries/freight-logistics.md` §7), and home healthcare scores
  7/8 but is explicitly the vertical to pilot *last*, not first
  (`../industries/home-healthcare.md` §9). Use this framework to decide
  **where to look**, not as a substitute for the vertical-specific
  caveats already written up once a market clears the threshold.

## 4. How to use this going forward

Any new "what about market X" question should get scored against these
four dimensions before a design doc gets written for it. A market scoring
low on negotiation surface or assistant-integration headroom specifically
should be deprioritized regardless of how large or appealing the market
looks in isolation — size without a real matching inefficiency to recover,
or with an incumbent already wired into the distribution layer that
matters most (§`04-scaling-to-billions-gtm-roadmap.md`), is not this
project's opportunity.
