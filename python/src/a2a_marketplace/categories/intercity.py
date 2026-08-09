"""Reference category plugin: intercity ride-pooling.

This is the ONLY file that knows what a "ride" is. It demonstrates how a
vertical plugs into the neutral engine by implementing the Category port:
grouping along a corridor, per-waypoint pricing, comfort-preference
compatibility for coalitions, and drop-confirmation evidence. Zomato, OLX,
etc. would each be a different file just like this — the engine never changes.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Iterable

from ..errors import ValidationError
from ..models import Intent, Money, Offer, Commitment


class IntercityTravelCategory:
    id = "intercity_travel"

    # -- validation -----------------------------------------------------------

    def validate_intent(self, intent: Intent) -> None:
        keys = intent.grouping_keys
        for k in ("source_region", "destination_region", "start_time_bucket"):
            if k not in keys:
                raise ValidationError(f"intent grouping_keys missing '{k}'")
        if "drop_stop" not in intent.preferences:
            raise ValidationError("intent.preferences must include 'drop_stop'")

    def validate_offer(self, offer: Offer) -> None:
        route = offer.category_ext.get("route")
        if not isinstance(route, list) or len(route) < 2:
            raise ValidationError("offer.category_ext.route must have >= 2 stops")

    # -- matching -------------------------------------------------------------

    def satisfies(self, intent: Intent, offer: Offer, now: datetime) -> bool:
        stop = self._route_stop(offer, intent.preferences["drop_stop"])
        if stop is None:
            return False  # this ride doesn't serve the rider's waypoint
        departure = self._departure(offer)
        if not intent.constraints.time_window.contains(departure):
            return False
        price = self.price_for(intent, offer)
        if not (price <= intent.constraints.budget_ceiling):
            return False
        return offer.capacity.remaining >= intent.constraints.quantity

    def price_for(self, intent: Intent, offer: Offer) -> Money:
        stop = self._route_stop(offer, intent.preferences["drop_stop"])
        if stop is None or "price_per_seat" not in stop:
            return offer.price.times(intent.constraints.quantity)
        pps = stop["price_per_seat"]
        per = pps if isinstance(pps, Money) else Money(pps["amount_minor"], pps["currency"])
        return per.times(intent.constraints.quantity)

    def compatible(self, intents: Iterable[Intent]) -> bool:
        """Comfort-preference compatibility, over abstract, declared traits.

        Each intent may declare ``preferences['traits']`` (what it *is*) and
        ``preferences['requires']`` (what co-passengers must be). A group
        clears only if every member's requirements hold for all members. This
        is deliberately generic — it encodes no assumptions about people.
        """
        members = list(intents)
        for m in members:
            requires = set(m.preferences.get("requires", []))
            if not requires:
                continue
            for other in members:
                if other is m:
                    continue
                traits = set(other.preferences.get("traits", []))
                if not requires.issubset(traits):
                    return False
        return True

    # -- fulfillment ----------------------------------------------------------

    def verify_evidence(self, commitment: Commitment, evidence: dict[str, Any]) -> bool:
        """P8 platform gate: every committed member must have a drop confirmed."""
        drops = evidence.get("dropoffs")
        if not isinstance(drops, list):
            return False
        confirmed = {d.get("intent_ref") for d in drops if d.get("confirmed_at")}
        expected = {d["intent_ref"] for d in commitment.detail.get("drops", [])}
        return expected.issubset(confirmed) and bool(expected)

    # -- internals ------------------------------------------------------------

    @staticmethod
    def _route_stop(offer: Offer, stop_name: str) -> dict[str, Any] | None:
        for stop in offer.category_ext.get("route", []):
            if stop.get("stop") == stop_name:
                return stop
        return None

    @staticmethod
    def _departure(offer: Offer) -> datetime:
        route = offer.category_ext.get("route", [])
        first = route[0]
        return first["eta"] if isinstance(first.get("eta"), datetime) else offer.created_at
