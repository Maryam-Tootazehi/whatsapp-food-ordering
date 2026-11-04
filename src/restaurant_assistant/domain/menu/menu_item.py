"""MenuItem entity: something a customer can order."""

from __future__ import annotations

from dataclasses import dataclass

from restaurant_assistant.domain.menu.allergen import Allergen, AllergenAnswer, AllergenDeclaration
from restaurant_assistant.domain.shared.money import Language, Money


@dataclass(eq=False)
class MenuItem:
    """An entity: it has an identity (id) that stays the same when its name or price changes."""

    id: str
    name: str
    category: str
    price: Money
    name_en: str | None = None
    aliases: tuple[str, ...] = ()
    available: bool = True
    allergens: AllergenDeclaration | None = None  # None = not confirmed by the owner

    def __post_init__(self) -> None:
        if not self.id.strip() or not self.name.strip():
            raise ValueError("A menu item needs an id and a name")

    def __eq__(self, other: object) -> bool:
        return isinstance(other, MenuItem) and other.id == self.id

    def __hash__(self) -> int:
        return hash(self.id)

    def display_name(self, language: Language) -> str:
        return self.name_en if language == "en" and self.name_en else self.name

    def mark_sold_out(self) -> None:
        self.available = False

    def mark_available(self) -> None:
        self.available = True

    def allergen_answer(self, allergen: Allergen) -> AllergenAnswer:
        if self.allergens is None:
            return AllergenAnswer.UNKNOWN
        return self.allergens.answer(allergen)
