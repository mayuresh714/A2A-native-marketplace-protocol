"""The kernel entities, mirroring ``schema/core/*``.

Business-neutral: nothing here mentions rides, food, or freight. The
category-specific shape lives in ``grouping_keys`` / ``preferences`` /
``category_ext`` dicts, validated by a :class:`~a2a_marketplace.ports.Category`
plugin — never by adding a field here.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

from .common import (
    AutonomyLevel,
    CoalitionStatus,
    CommitmentStatus,
    DisputeOutcome,
    DisputeStatus,
    EscrowState,
    FulfillmentOutcome,
    Money,
    PriceRule,
    ProposalStatus,
    Stance,
    TimeWindow,
)

# Grouping keys are a small, hashable, coarse mapping. We key partitions on a
# sorted tuple of their items so nothing participant-specific leaks in (P3).
GroupingKeys = dict[str, str]


def partition_of(keys: GroupingKeys) -> tuple[tuple[str, str], ...]:
    return tuple(sorted(keys.items()))


@dataclass(slots=True)
class Mandate:
    mandate_id: str
    principal_ref: str
    holder_ref: str
    category_ref: str
    budget_ceiling: Money
    autonomy_level: AutonomyLevel = AutonomyLevel.REQUIRE_CONFIRMATION
    valid_until: datetime | None = None


@dataclass(slots=True)
class Agent:
    agent_id: str  # a DID
    principal_ref: str
    service_categories: list[str]
    stances: dict[str, list[Stance]]
    coalition_capable: dict[str, bool] = field(default_factory=dict)
    attestation_refs: list[str] = field(default_factory=list)


@dataclass(slots=True)
class Constraints:
    """Tier 2 (P3): hard, must-satisfy requirements applied as filters."""

    time_window: TimeWindow
    budget_ceiling: Money
    quantity: int = 1
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class Intent:
    intent_id: str
    issuer_ref: str
    category_ref: str
    grouping_keys: GroupingKeys  # Tier 1 (P3): coarse, shared, partitioning
    constraints: Constraints
    mandate_ref: str
    created_at: datetime  # FIFO ordering key (P6)
    expiry: datetime
    preferences: dict[str, Any] = field(default_factory=dict)  # Tier 3 (P3)
    coalition_opt_in: bool = False
    solo_wait_seconds: int = 0
    """How long this intent waits for a SOLO match before it's eligible to
    move to the collaboration queue (P12). 0 = escalate immediately on the
    first failed solo attempt."""
    matched: bool = False

    @property
    def partition(self) -> tuple[tuple[str, str], ...]:
        return partition_of(self.grouping_keys)

    def collaboration_eligible_at(self) -> datetime:
        return self.created_at + timedelta(seconds=self.solo_wait_seconds)


@dataclass(slots=True)
class Capacity:
    unit: str
    quantity: int
    min_fill: int = 1  # minimum total units required to activate the offer
    remaining: int = -1  # set in __post_init__

    def __post_init__(self) -> None:
        if self.remaining < 0:
            self.remaining = self.quantity


@dataclass(slots=True)
class Offer:
    offer_id: str
    issuer_ref: str
    category_ref: str
    grouping_keys: GroupingKeys
    capacity: Capacity
    price: Money  # headline per-unit price; category may refine per-request
    hold_expires_at: datetime
    created_at: datetime
    negotiable: bool = True
    category_ext: dict[str, Any] = field(default_factory=dict)
    attestation_refs: list[str] = field(default_factory=list)
    requires_explicit_approval: bool = False
    """If False (default), posting this offer IS the provider's blanket
    approval for any matching demand — a match proposal auto-approves on the
    provider side. A higher-stakes category can set True to require the
    provider to explicitly approve each individual staged match (P11)."""
    provider_stake: Money | None = None
    """Optional per-match deposit the provider also puts up (P11: "each
    party putting money"). Category-defined; most categories leave this None."""

    @property
    def partition(self) -> tuple[tuple[str, str], ...]:
        return partition_of(self.grouping_keys)


@dataclass(slots=True)
class Coalition:
    coalition_id: str
    member_intent_refs: list[str]
    proposed_departure: datetime
    total_price: Money
    price_rule: PriceRule = PriceRule.ADDITIVE
    stance: Stance = Stance.DEMAND  # v0: demand only (P1)
    status: CoalitionStatus = CoalitionStatus.FORMING

    def __post_init__(self) -> None:
        # Enforce the anti-cartel rule structurally, mirroring the schema const.
        if self.stance is not Stance.DEMAND:
            raise ValueError(
                "supply-side coalitions are disabled by default (P1); "
                "provider bundling is a governance-gated exception, not v0"
            )


@dataclass(slots=True)
class MatchProposal:
    """A staged match (P11): created the instant demand and supply are found
    compatible, but NOT yet binding. Becomes a Commitment only once both
    sides have approved and funds are captured — see MarketplaceEngine."""

    proposal_id: str
    offer_ref: str
    demand_ref: str
    demand_kind: str  # "intent" | "coalition"
    demand_agents: list[str]
    supply_agent: str
    total_price: Money
    departure: datetime
    quantity: int
    detail: dict[str, Any]
    mandate_refs: list[str]
    created_at: datetime
    respond_by: datetime
    status: ProposalStatus = ProposalStatus.PROPOSED
    consumer_approved: bool | None = None
    provider_approved: bool | None = None


@dataclass(slots=True)
class Escrow:
    amount: Money  # consumer payment held
    state: EscrowState = EscrowState.AUTHORIZED
    provider_stake: Money | None = None  # optional provider deposit held alongside


@dataclass(slots=True)
class Commitment:
    commitment_id: str
    offer_ref: str
    demand_ref: str
    demand_kind: str  # "intent" | "coalition"
    supply_agent: str
    demand_agents: list[str]
    total_price: Money
    departure: datetime
    escrow: Escrow
    mandate_refs: list[str]
    created_at: datetime
    status: CommitmentStatus = CommitmentStatus.HELD
    """HELD here means 'agreement reached, funds in platform custody' — an
    agreement, not the final step (P11). Completion is a separate gate (P8)."""
    detail: dict[str, Any] = field(default_factory=dict)
    fulfillment_window: TimeWindow | None = None
    """The service's own duration — a minute to multiple days (P13). None
    means the category treats fulfillment as effectively instantaneous."""


@dataclass(slots=True)
class Fulfillment:
    fulfillment_id: str
    commitment_ref: str
    consumer_approved: bool
    provider_approved: bool
    platform_verified: bool
    outcome: FulfillmentOutcome
    evidence: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class Settlement:
    settlement_id: str
    commitment_ref: str
    fulfillment_ref: str
    gross: Money
    protocol_fee: Money
    net_to_provider: Money
    released_at: datetime


@dataclass(slots=True)
class Dispute:
    """Raisable by either party at ANY point in the fulfillment window
    (docs/spec/05). The protocol guarantees the state machine and the
    freeze; the resolution POLICY is Layer C / operator territory."""

    dispute_id: str
    commitment_ref: str
    raised_by: str  # "consumer" | "provider"
    reason_code: str
    raised_at: datetime
    status: DisputeStatus = DisputeStatus.OPEN
    outcome: DisputeOutcome | None = None
    payouts: dict[str, Money] = field(default_factory=dict)
    resolved_at: datetime | None = None
