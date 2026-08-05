# Open source, licensing, and governance

The project should be open source — that's a stated goal, and it's also
the *right* goal, because everything in `01`-`03` only works if
independent parties trust the substrate enough to self-host it and build
on it. But "open source" is a set of specific, consequential choices, not
a single switch. This doc works through them and reconciles open-sourcing
the core with having any defensible business at all.

## 1. Why open source is load-bearing here, not just ideological

- **Adoption/trust.** A distribution platform (`02` §5) won't build its
  supply graph on a proprietary substrate it can't inspect, fork, or run
  without a vendor — the lock-in risk is exactly what they're trying to
  avoid by not just using an incumbent. Open source removes that objection;
  it's the precondition for the self-hostable promise being credible.
- **Neutrality.** Federation (`03`) requires competitors to run compatible
  networks. They won't converge on a standard controlled by one private
  company's closed code — an open, independently-governed protocol is the
  only kind competitors co-adopt (the reason A2A/AP2 themselves are open).
- **Anti-fragmentation via a canonical implementation.** Open standards rot
  into incompatible dialects without a reference (`../technical-deep-dive/
  06` §5). A canonical open-source implementation + conformance suite is
  the antidote — and it can only be canonical if it's open.

## 2. The open-core split (what's open vs. what's commercial)

The honest reconciliation of "open source" with "a business" is the
**open-core** model, and the split follows the layering from `01`:

| Component | Openness | Rationale |
|---|---|---|
| **Protocol spec** (Layer 1) | Fully open, permissive | It's a standard; closing it defeats the purpose |
| **Reference implementation + SDKs + adapters** (the reference stack, `01` §5) | Fully open | The adoption engine; must be forkable/self-hostable to be trusted |
| **Conformance test suite** | Fully open | Anyone must be able to prove compliance |
| **Managed NaaS** (hosted control/data plane, `02`) | Commercial service | Convenience, not lock-in — self-host is always available |
| **Inter-network utility** (identity/trust roots, discovery directory, cross-network settlement, certification — `03` §7) | Commercial / consortium-governed service | The neutral seat between networks; the actual moat (`../business-strategy/06`) |
| **Enterprise add-ons** (SLA, support, compliance tooling, private-deployment assistance) | Commercial | Standard open-core monetization |

The core is open; money comes from *operating* the neutral inter-network
layer and from *managed convenience* — never from closing the substrate.
This is the same shape as successful open-core infra companies (the code
is open and self-hostable; the managed cloud and the cross-org network
services are paid), and it's directly consistent with
`../business-strategy/06`'s conclusion that the two ownable layers are
liquidity and neutral clearing — both of which live *above* the open core,
not inside it.

## 3. Which license (the specific, consequential choice)

Two real options, with a genuine trade-off:

- **Permissive (Apache-2.0).** Maximizes adoption and standard-setting;
  anyone (including big clouds) can use and offer it. Best when the goal is
  *ubiquity of the protocol* and the moat is elsewhere (liquidity, the
  neutral layer — which it is here). Apache-2.0 specifically (over MIT) for
  its explicit patent grant, which matters for a protocol meant to become
  infrastructure. **Recommended for the protocol + SDKs.**
- **Protective (AGPL, or a source-available license like BSL/SSPL).**
  Guards against a hyperscaler taking the reference stack and offering a
  competing managed service without contributing back — the "strip-mining"
  concern that pushed several infra companies to relicense. The cost is
  reduced adoption and standards-friendliness (some orgs can't touch
  copyleft/source-available), which is a real hit for something whose whole
  value is becoming a *standard*.

**Recommended posture:** Apache-2.0 for the protocol, SDKs, and client
libraries (ubiquity is the point, and you *want* even competitors adopting
the wire format). Consider a protective license (AGPL or BSL with a time-
delay to open) only for the *server reference stack* if hyperscaler
strip-mining of the managed offering becomes a live threat — a split
several projects use deliberately. This is a reversible-later decision to
flag, not lock in prematurely; over-protecting early is the bigger risk to
a standard than under-protecting.

## 4. Governance (who controls the standard)

A protocol meant to be co-adopted by competitors (`03`) cannot be seen as
one company's asset, or competitors won't build on it — this is the
central governance tension, already flagged in `../business-strategy/05-
open-business-issues.md` and `../technical-deep-dive/05` §1. The credible
paths:

- **Company-led initially, foundation-donated later** — the common,
  realistic arc: one company builds and stewards it to establish
  direction and momentum, then donates the *protocol and reference
  implementation* to a neutral foundation (the A2A→Linux Foundation path
  this project already cites as precedent) once adoption justifies it,
  while retaining a commercial entity that operates the managed/inter-
  network services on top. This separates *the standard* (neutrally
  governed, un-ownable) from *the business* (a company operating services
  above it) — which is exactly the open-core split in §2 expressed
  organizationally.
- **Consortium from the start** — more credibly neutral immediately, but
  slower and harder to bootstrap; usually only viable once there are
  already several committed large players, which is a later-stage
  condition.

The unavoidable tension (stated, not solved): the more neutral the
governance, the less any single company controls — including the company
that built it. This is the same neutrality-vs-capture tension as
`../business-strategy/06` §8, now at the governance layer. It doesn't have
a clean resolution; it's a deliberate trade of control for adoption, and
for a standard that only has value if competitors co-adopt it, trading
control for adoption is usually the correct direction — but it should be
an eyes-open choice.

## 5. Conformance and certification (the anti-fragmentation control point)

The one place a neutral operator retains legitimate leverage *without*
closing anything: **certification.** A "conformant network" mark, granted
by passing the open conformance suite (`01` §5) and meeting the trust-
framework requirements (`03` §4), is:

- what gates a network into the federated trust graph (`03` §6),
- a legitimate quality/interoperability signal (like a standards
  certification or a CA being in the trust store),
- a governance lever to keep the ecosystem from fragmenting into
  incompatible forks — "fork all you like, but an uncertified fork doesn't
  federate."

This is fully compatible with open source (the code and tests are open;
the *certification and the federated trust graph* are the governed asset)
and is a cleaner, more defensible control point than any licensing
restriction — it protects interoperability (the thing users actually care
about) rather than protecting code (which openness gives away by design).

## 6. The one-paragraph reconciliation

Open-source the protocol, the reference stack, the SDKs, and the
conformance suite under a permissive license — that's the adoption and
neutrality engine, and it's un-monetizable by design and on purpose.
Monetize by *operating* the two things that sit above the open substrate
and that a neutral party is uniquely positioned to run: managed
deployment convenience (`02`), and the inter-network federation utility —
identity/trust roots, discovery, cross-network settlement, and
certification (`03` §7). Govern the standard toward a neutral foundation
as it matures, keeping a commercial entity operating the services on top.
This gives away exactly what has to be given away for the vision to work
(the substrate), keeps exactly what can be defensibly kept (liquidity, the
neutral inter-network seat, certification), and matches — rather than
contradicts — every prior conclusion in `../business-strategy/` and
`../technical-deep-dive/05` about where this project's real, honest moat
lives.
