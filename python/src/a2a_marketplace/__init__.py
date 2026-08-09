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


def dev_engine(fee_bps: int = 200, clock=None) -> MarketplaceEngine:
    """A fully-wired engine using in-memory reference adapters and the
    intercity category. For development, tests, and simulation only."""
    from .adapters import (
        AllowAllIdentity,
        InMemoryStorage,
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
        fee_bps=fee_bps,
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
