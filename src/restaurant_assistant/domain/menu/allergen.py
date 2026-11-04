"""Allergens (EU Regulation 1169/2011) and the owner's confirmed declaration for a dish."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import Enum, StrEnum


class Allergen(StrEnum):
    """The 14 allergens restaurants in the EU must be able to inform customers about."""

    GLUTEN = "gluten"
    CRUSTACEANS = "crustaceans"
    EGGS = "eggs"
    FISH = "fish"
    PEANUTS = "peanuts"
    SOYBEANS = "soybeans"
    MILK = "milk"
    NUTS = "nuts"
    CELERY = "celery"
    MUSTARD = "mustard"
    SESAME = "sesame"
    SULPHITES = "sulphites"
    LUPIN = "lupin"
    MOLLUSCS = "molluscs"

    @property
    def italian(self) -> str:
        return _ITALIAN[self]


_ITALIAN: dict[Allergen, str] = {
    Allergen.GLUTEN: "glutine",
    Allergen.CRUSTACEANS: "crostacei",
    Allergen.EGGS: "uova",
    Allergen.FISH: "pesce",
    Allergen.PEANUTS: "arachidi",
    Allergen.SOYBEANS: "soia",
    Allergen.MILK: "latte",
    Allergen.NUTS: "frutta a guscio",
    Allergen.CELERY: "sedano",
    Allergen.MUSTARD: "senape",
    Allergen.SESAME: "sesamo",
    Allergen.SULPHITES: "anidride solforosa e solfiti",
    Allergen.LUPIN: "lupini",
    Allergen.MOLLUSCS: "molluschi",
}


class AllergenAnswer(Enum):
    """What the assistant may say. There is deliberately no "SAFE" or "FREE_FROM"."""

    CONTAINS = "contains"
    MAY_CONTAIN = "may_contain"  # traces / cross-contamination declared by the owner
    NOT_DECLARED = "not_declared"  # confirmed list exists and this allergen is not on it
    UNKNOWN = "unknown"  # no confirmed data: hand over to staff


@dataclass(frozen=True, slots=True)
class AllergenDeclaration:
    """Allergens of one dish as confirmed by the owner. A value object: no identity of its own."""

    contains: frozenset[Allergen]
    confirmed_by: str
    confirmed_on: date
    may_contain: frozenset[Allergen] = field(default_factory=frozenset)

    def __post_init__(self) -> None:
        if not self.confirmed_by.strip():
            raise ValueError("An allergen declaration must say who confirmed it")

    def answer(self, allergen: Allergen) -> AllergenAnswer:
        if allergen in self.contains:
            return AllergenAnswer.CONTAINS
        if allergen in self.may_contain:
            return AllergenAnswer.MAY_CONTAIN
        return AllergenAnswer.NOT_DECLARED
