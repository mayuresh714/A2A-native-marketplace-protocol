# Home healthcare — non-emergency nursing, physiotherapy, elder-care visits

## 1. Why this fits the pattern

Same perishable-capacity, many-independent-providers structure as every
other vertical here (a nurse or physiotherapist's day has a fixed number
of visit-slots), but this doc exists specifically to find the **lower
bound on agent autonomy** — every design choice elsewhere in this project
defaults toward more automation; this vertical is the test of where the
protocol must default toward *less*, because the cost of a bad match is a
vulnerable person's health and safety, not a late dinner or an
over-detoured ride.

## 2. Today's pain

- **Patient/family side:** arranging a recurring home visit (post-surgery
  nursing, elder daily care, physiotherapy) today usually means a phone
  call to an agency, a scheduling back-and-forth by phone, and little
  visibility into who exactly is coming, their specific qualifications for
  this specific condition, or whether the same caregiver will return
  (continuity matters medically and emotionally for this category more
  than almost any other in this folder).
- **Provider side:** independent nurses/physiotherapists and small home-care
  agencies juggle schedules across many clients with narrow,
  medically-driven time windows (post-op wound care has to happen on a
  schedule, not "whenever"), and have little dynamic way to fill a
  cancellation slot with another client who needs exactly that skill set
  nearby.

## 3. Actors / provider types

- **Consumer agent** — represents the patient or (often) a family member
  arranging care on someone else's behalf — an important twist versus
  every other vertical here: the agent's principal and the service
  recipient are frequently different people, which changes who the mandate
  and consent flow needs to represent.
- **Provider agent types:**
  - *Independent licensed nurse/physiotherapist* — negotiates schedule,
    generally not price (often insurance/scheme-set or agency-set).
  - *Home-care agency* — dispatches from a pool of credentialed staff;
    agent represents "we have a qualified match in this window," similar
    in shape to the home-services small-firm dispatch agent.
  - *Insurance/scheme adjudicator* (where relevant) — not quite a provider,
    but a required party whose approval may gate whether a visit is
    payable at all; the protocol needs a slot for this kind of
    "authorization required before commitment" party that pure commercial
    verticals don't have.

## 4. Market structure

Price is frequently **not actually negotiable** by the provider agent at
all — set by insurance/scheme rate schedules or agency policy — so this
vertical exercises the "quote-and-book, not negotiate" role the main doc
assigned to fixed-schedule providers like railways, but for a very
different reason (regulatory/payer-set pricing, not fixed-infrastructure
economics). What *is* negotiable: time window, which specific credentialed
person, and continuity (same caregiver next visit).

## 5. Worked example

A family member is arranging twice-daily wound-care visits for a parent
recovering from surgery, for the next two weeks.

1. Consumer agent (family member's agent, principal ≠ care recipient)
   posts intent: skill required = post-surgical wound care, twice daily
   for 14 days, morning window 7-9am / evening window 6-8pm, insurance
   scheme reference attached, continuity strongly preferred.
2. Two independent nurses and one agency respond. The agency's offer
   includes an attestation bundle stronger than the other verticals in
   this folder require by default: license verification, background
   check, and — specific to this vertical — proof of current registration
   in good standing with the relevant medical board, refreshed
   periodically rather than checked once.
3. Consumer agent evaluates not just price/time fit but a
   **continuity constraint** absent elsewhere in this folder: it strongly
   weights an offer that can commit the *same* named nurse to all 28
   visits over offers that would rotate staff, even at a modestly higher
   price, because continuity of caregiver is a real clinical/comfort
   factor for this category specifically.
4. Insurance/scheme adjudicator agent (or a simple rules check, if the
   scheme is simple enough not to need a full agent) confirms the visits
   are within covered scope before the commitment is finalized — a
   pre-commitment gate the other verticals in this folder don't have.
5. Commitment finalizes, but — unlike the home-services example where a
   scope change auto-confirmed under a pre-authorized ceiling — **every
   individual visit here still gets a human (family member) notification
   and easy-cancel window**, even though the schedule was already agreed
   two weeks out, because ongoing in-home medical care is exactly the
   category where "the agent quietly handled it" should not extend to
   silently continuing a recurring in-home visit arrangement without
   periodic human awareness.

## 6. Coalition/pooling angle

Deliberately minimal to none by default. Unlike the food-delivery or
travel pooling cases, batching unrelated patients' visits for provider
routing efficiency is defensible (a nurse visiting two nearby patients
back-to-back is fine and already how home-care routing works today), but
**patient-facing coalition formation (the equivalent of the travel doc's
consumer coalition) does not apply here** — there is no version of "merge
two patients' care into one shared visit" that makes sense, since the
service is inherently personal and non-shareable. Where provider-side
route-batching is used (nurse visiting patient A then patient B nearby),
it must never leak either patient's identity, condition, or schedule to
the other patient's agent — a stricter data-isolation requirement than the
provider-side batching described in the home-services doc.

## 7. Price discovery / anti-cartel considerations

Muted relative to every other vertical here, precisely because price is
usually payer-set rather than provider-negotiated (§4) — there's less
surface for provider agents to collude on price specifically. The more
realistic risk in this vertical is **availability gatekeeping**: a small
number of credentialed providers in a region for a specialized skill
(e.g., pediatric home nursing) could functionally act as a cartel on
*availability/priority* even without touching price — e.g., systematically
deprioritizing lower-paying insurance schemes' patients in favor of
private-pay patients. Worth a specific monitoring signal (are covered-care
patients systematically getting worse time slots or longer waits than
equivalent private-pay patients from the same providers), distinct from
the price-band monitoring the other docs describe.

## 8. Trust, safety & compliance caveats

- **The strictest verticals for regulatory compliance in this entire
  folder.** Medical licensing, health-data privacy regulations (which
  vary sharply by country/region), and mandatory reporting obligations
  all apply, and none of this can be treated as a "review before shipping"
  afterthought the way the main doc flagged for the travel comfort
  preferences — it has to be a hard architectural constraint (e.g., health
  information should not transit through a general-purpose registry or
  discovery layer at all; only credential attestation status should be
  visible pre-match).
- **Principal-vs-recipient consent.** Because the person arranging care is
  often not the person receiving it (§3), the protocol needs an explicit
  representation of "who consented to this" that's distinct from "who is
  paying" and distinct again from "who is receiving care" — three
  potentially different people, and the mandate model needs to capture
  which of them authorized what.
- **No silent recurring auto-commit (§5, step 5).** This is the one
  vertical in this folder where the default should tilt away from
  autonomy even for a schedule the human already approved — recurring
  in-home medical visits should surface for periodic human awareness, not
  just initial approval.

## 9. Why this could be high impact

Aging populations and rising post-acute home-care demand make this a
structurally growing need across many markets, the current arrangement
process (phone-tag with agencies, low visibility into which specific
credentialed person is coming) is a genuine, currently under-addressed
pain point for families already dealing with a stressful health situation,
and the fragmented independent-provider supply side (many small agencies
and independent licensed practitioners, no single dominant platform in
most regions) again fits the decentralized-matching shape this protocol
targets — with the explicit caveat that this vertical should be the last
one piloted, not the first, given how much conservatism §5 and §8 require
relative to the rest of this folder.
