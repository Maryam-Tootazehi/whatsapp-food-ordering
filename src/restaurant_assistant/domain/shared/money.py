"""Money value object: an amount of euro cents. See ADR 0003."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Literal

Language = Literal["it", "en"]


@dataclass(frozen=True, slots=True)
class Money:
    """Immutable amount in cents. Two Money objects are equal when their values are equal."""

    cents: int
    currency: str = "EUR"

    def __post_init__(self) -> None:
        # bool is a subclass of int in Python, so exclude it explicitly.
        if not isinstance(self.cents, int) or isinstance(self.cents, bool):
            raise TypeError(f"Money needs whole cents as int, got {self.cents!r}")
        if self.cents < 0:
            raise ValueError("Money cannot be negative")

    @classmethod
    def zero(cls, currency: str = "EUR") -> Money:
        return cls(0, currency)

    @classmethod
    def from_euros(cls, text: str, currency: str = "EUR") -> Money:
        """Parse "8.50", "8,50" or "12" exactly, via Decimal (never float)."""
        try:
            amount = Decimal(text.strip().replace(",", "."))
        except InvalidOperation as exc:
            raise ValueError(f"Not an amount: {text!r}") from exc
        cents = amount * 100
        if cents != cents.to_integral_value():
            raise ValueError(f"More than two decimals: {text!r}")
        return cls(int(cents), currency)

    @classmethod
    def total(cls, amounts: Iterable[Money], currency: str = "EUR") -> Money:
        result = cls.zero(currency)
        for amount in amounts:
            result = result + amount
        return result

    def __add__(self, other: Money) -> Money:
        if self.currency != other.currency:
            raise ValueError(f"Cannot add {self.currency} and {other.currency}")
        return Money(self.cents + other.cents, self.currency)

    def __mul__(self, quantity: int) -> Money:
        if not isinstance(quantity, int) or isinstance(quantity, bool) or quantity < 0:
            raise ValueError(f"Quantity must be a whole number >= 0, got {quantity!r}")
        return Money(self.cents * quantity, self.currency)

    __rmul__ = __mul__

    def format(self, language: Language) -> str:
        """19,50 € for Italian customers, €19.50 for English ones (euro only for now)."""
        euros, cents = divmod(self.cents, 100)
        if language == "it":
            return f"{euros:,}".replace(",", ".") + f",{cents:02d} €"
        return f"€{euros:,}.{cents:02d}"
