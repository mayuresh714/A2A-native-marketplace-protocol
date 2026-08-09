"""The kernel entities, mirroring ``schema/core/*``.

Business-neutral: nothing here mentions rides, food, or freight. The
category-specific shape lives in ``grouping_keys`` / ``preferences`` /
``category_ext`` dicts, validated by a :class:`~a2a_marketplace.ports.Category`
plugin — never by adding a field here.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from .common import (
    AutonomyLevel,
    CoalitionStatus,
    CommitmentStatus,
    EscrowState,
    FulfillmentOutcome,
    Money,
    PriceRule,
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
    matched: bool = False

    @property
    def partition(self) -> tuple[tuple[str, str], ...]:
        return partition_of(self.grouping_keys)


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
class Escrow:
    amount: Money
    state: EscrowState = EscrowState.AUTHORIZED


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
    detail: dict[str, Any] = field(default_factory=dict)


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
