"""How much the kitchen can prepare in one slot."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class KitchenCapacity:
    """Max kitchen items per slot (e.g. pizzas per 15 minutes). The owner meeting decides
    what counts as an item (drinks probably don't) and the real number."""

    max_items_per_slot: int
    slot_minutes: int = 15

    def __post_init__(self) -> None:
        if self.max_items_per_slot <= 0:
            raise ValueError("Capacity must be positive")

    def has_room(self, already_planned: int, extra: int) -> bool:
        return already_planned + extra <= self.max_items_per_slot
