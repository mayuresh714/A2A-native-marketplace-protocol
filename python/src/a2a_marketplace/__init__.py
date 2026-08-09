"""a2a_marketplace — an open, business-neutral protocol implementation for
agent-mediated marketplaces.

Quick start::

    from a2a_marketplace import MarketplaceEngine, dev_engine
    engine = dev_engine()  # in-memory adapters + intercity category

The engine is neutral mechanism; you plug in your own storage, ranking,
escrow, and identity via the ``ports`` interfaces. See the README.
"""
from .engine import MarketplaceEngine
from .version import PROTOCOL_VERSION, __version__
from . import adapters, models, ports
from .categories import IntercityTravelCategory


def dev_engine(fee_bps: int = 200, clock=None, proposal_ttl_seconds: int = 900) -> MarketplaceEngine:
    """A fully-wired engine using in-memory reference adapters and the
    intercity category. For development, tests, and simulation only."""
    from .adapters import (
        AllowAllFraudFilter,
        AllowAllIdentity,
        AlwaysEscalateResolver,
        InMemoryStorage,
        LoggingNotifier,
        PriceAscRanking,
        SimEscrow,
        SystemClock,
    )

    cat = IntercityTravelCategory()
    return MarketplaceEngine(
        storage=InMemoryStorage(),
        clock=clock or SystemClock(),
        ranking=PriceAscRanking(),
        escrow=SimEscrow(),
        identity=AllowAllIdentity(),
        categories={cat.id: cat},
        fraud_filter=AllowAllFraudFilter(),
        notifier=LoggingNotifier(),
        dispute_resolver=AlwaysEscalateResolver(),
        fee_bps=fee_bps,
        proposal_ttl_seconds=proposal_ttl_seconds,
    )


__all__ = [
    "MarketplaceEngine",
    "dev_engine",
    "IntercityTravelCategory",
    "adapters",
    "models",
    "ports",
    "PROTOCOL_VERSION",
    "__version__",
]
