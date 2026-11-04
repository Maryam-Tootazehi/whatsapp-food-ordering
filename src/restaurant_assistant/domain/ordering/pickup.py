"""PickupPolicy domain service: can we promise this pickup time? (story O1)

Pure function of its inputs. `now` is passed in (no hidden clock) and the current kitchen load
comes in as a function, so the domain never touches the database and tests are deterministic.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum

from restaurant_assistant.domain.kitchen.capacity import KitchenCapacity
from restaurant_assistant.domain.shared.opening_hours import OpeningHours
from restaurant_assistant.domain.shared.slot import Slot

SlotLoad = Callable[[Slot], int]
"""Items already planned in a slot. The application builds this from ONE database query."""


class Refusal(Enum):
    IN_THE_PAST = "in_the_past"
    TOO_SOON = "too_soon"
    CLOSED = "closed"
    TOO_LARGE = "too_large"  # bigger than a whole slot: staff should handle it
    KITCHEN_FULL = "kitchen_full"


@dataclass(frozen=True, slots=True)
class PickupAccepted:
    slot: Slot
    pickup_at: datetime


@dataclass(frozen=True, slots=True)
class PickupRefused:
    reason: Refusal
    alternatives: tuple[Slot, ...] = ()


PickupDecision = PickupAccepted | PickupRefused


@dataclass(frozen=True)
class PickupPolicy:
    opening_hours: OpeningHours
    capacity: KitchenCapacity
    lead_time: timedelta = timedelta(minutes=20)
    max_suggestions: int = 3
    search_days: int = 2

    def check(
        self, requested: datetime, *, now: datetime, items: int, load: SlotLoad
    ) -> PickupDecision:
        if items <= 0:
            raise ValueError("An order needs at least one item")
        if items > self.capacity.max_items_per_slot:
            return PickupRefused(Refusal.TOO_LARGE)  # no slot can ever fit it: hand to staff
        tz = self.opening_hours.timezone
        requested, now = requested.astimezone(tz), now.astimezone(tz)
        slot = Slot.containing(requested, self.capacity.slot_minutes)
        earliest = now + self.lead_time

        reason: Refusal | None = None
        if requested < now:
            reason = Refusal.IN_THE_PAST
        elif requested < earliest:
            reason = Refusal.TOO_SOON
        elif self.opening_hours.service_for(slot) is None:
            reason = Refusal.CLOSED
        elif not self.capacity.has_room(load(slot), items):
            reason = Refusal.KITCHEN_FULL

        if reason is None:
            return PickupAccepted(slot, requested)
        return PickupRefused(reason, self._alternatives(slot, earliest, items, load))

    def _alternatives(
        self, slot: Slot, earliest: datetime, items: int, load: SlotLoad
    ) -> tuple[Slot, ...]:
        first_possible = Slot.containing(earliest, self.capacity.slot_minutes)
        if first_possible.start < earliest:
            first_possible = first_possible.next()
        candidate = max(slot, first_possible)
        horizon = candidate.start + timedelta(days=self.search_days)
        found: list[Slot] = []
        while len(found) < self.max_suggestions and candidate.start < horizon:
            if self.opening_hours.service_for(candidate) and self.capacity.has_room(
                load(candidate), items
            ):
                found.append(candidate)
            candidate = candidate.next()
        return tuple(found)
