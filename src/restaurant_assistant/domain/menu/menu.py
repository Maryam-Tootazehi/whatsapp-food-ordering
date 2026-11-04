"""Menu aggregate: the whole set of dishes, and the rules that span more than one dish."""

from __future__ import annotations

from collections.abc import Iterable, Iterator

from restaurant_assistant.domain.menu.menu_item import MenuItem
from restaurant_assistant.domain.menu.text import normalize


class MenuError(ValueError):
    """The menu breaks one of its rules (duplicate id, alias used by two dishes)."""


class Menu:
    """Aggregate root. Rules it protects:

    - every dish id is unique;
    - a name or alias (after normalisation) points to exactly one dish, so matching can never
      silently pick between two dishes.
    """

    def __init__(self, items: Iterable[MenuItem]) -> None:
        self._items: dict[str, MenuItem] = {}
        owner_of_name: dict[str, str] = {}
        for dish in items:
            if dish.id in self._items:
                raise MenuError(f"Duplicate menu item id: {dish.id}")
            self._items[dish.id] = dish
            for label in (dish.name, dish.name_en, *dish.aliases):
                if not label:
                    continue
                key = normalize(label)
                other = owner_of_name.setdefault(key, dish.id)
                if other != dish.id:
                    raise MenuError(f"'{key}' is used by both {other} and {dish.id}")

    def __iter__(self) -> Iterator[MenuItem]:
        return iter(self._items.values())

    def __len__(self) -> int:
        return len(self._items)

    def find(self, item_id: str) -> MenuItem | None:
        return self._items.get(item_id)

    def get(self, item_id: str) -> MenuItem:
        return self._items[item_id]

    def available_items(self) -> list[MenuItem]:
        return [dish for dish in self if dish.available]
