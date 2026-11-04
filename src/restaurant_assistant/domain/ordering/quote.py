"""The summary shown to the customer is a snapshot, not an order or a capacity reservation.

Only matched menu ids and quantities enter here. No prices supplied by the model are accepted.
Ten minutes is a provisional quote lifetime, not an owner-confirmed rule.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from restaurant_assistant.domain.menu.menu import Menu
from restaurant_assistant.domain.ordering.errors import OrderError, OrderProblem
from restaurant_assistant.domain.ordering.pickup import PickupPolicy, PickupRefused, SlotLoad
from restaurant_assistant.domain.shared.money import Money


def aware_utc(moment: datetime) -> datetime:
    """Reject ambiguous naive datetimes; compare elapsed time in UTC, including across DST."""
    if moment.tzinfo is None or moment.utcoffset() is None:
        raise ValueError("A time zone is required")
    return moment.astimezone(UTC)


def positive_quantity(quantity: int) -> None:
    if type(quantity) is not int or quantity <= 0:
        raise ValueError("Quantity must be a positive whole number")


@dataclass(frozen=True, slots=True)
class RequestedItem:
    item_id: str
    quantity: int

    def __post_init__(self) -> None:
        if not self.item_id.strip():
            raise ValueError("An item id is required")
        positive_quantity(self.quantity)


@dataclass(frozen=True, slots=True)
class OrderLine:
    """Immutable dish name and price at the time of the summary."""

    item_id: str
    name: str
    quantity: int
    unit_price: Money

    def __post_init__(self) -> None:
        if not self.item_id.strip() or not self.name.strip():
            raise ValueError("A line needs an item id and a name")
        positive_quantity(self.quantity)
        if self.unit_price.currency != "EUR":
            raise ValueError("The pilot only supports EUR")

    @property
    def subtotal(self) -> Money:
        return self.unit_price * self.quantity


@dataclass(frozen=True, slots=True)
class Quote:
    id: str
    lines: tuple[OrderLine, ...]
    pickup_at: datetime
    issued_at: datetime
    expires_at: datetime

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("A quote id is required")
        if not isinstance(self.lines, tuple):
            raise ValueError("Quote lines must be an immutable tuple")
        if not self.lines:
            raise OrderError(OrderProblem.EMPTY_ORDER)
        if len({line.item_id for line in self.lines}) != len(self.lines):
            raise ValueError("Combine repeated item ids before constructing a quote")
        if aware_utc(self.expires_at) <= aware_utc(self.issued_at):
            raise ValueError("Expiry must be after issue time")
        if aware_utc(self.pickup_at) <= aware_utc(self.issued_at):
            raise ValueError("Pickup must be after issue time")

    @property
    def total(self) -> Money:
        return Money.total(line.subtotal for line in self.lines)

    @property
    def item_count(self) -> int:
        # Provisional: all quantities count. The owner must define which dishes use capacity.
        return sum(line.quantity for line in self.lines)

    @classmethod
    def build(
        cls,
        *,
        quote_id: str,
        requested: tuple[RequestedItem, ...],
        menu: Menu,
        pickup_at: datetime,
        now: datetime,
        policy: PickupPolicy,
        load: SlotLoad,
        lifetime: timedelta = timedelta(minutes=10),
    ) -> Quote:
        aware_utc(pickup_at)
        issued_utc = aware_utc(now)
        if lifetime <= timedelta(0):
            raise ValueError("Quote lifetime must be positive")
        if not requested:
            raise OrderError(OrderProblem.EMPTY_ORDER)
        quantities: dict[str, int] = {}
        for request in requested:
            quantities[request.item_id] = quantities.get(request.item_id, 0) + request.quantity
        lines = []
        for item_id, quantity in quantities.items():
            dish = menu.find(item_id)
            if dish is None:
                raise OrderError(OrderProblem.UNKNOWN_ITEM)
            if not dish.available:
                raise OrderError(OrderProblem.UNAVAILABLE_ITEM)
            lines.append(OrderLine(dish.id, dish.name, quantity, dish.price))
        decision = policy.check(pickup_at, now=now, items=sum(quantities.values()), load=load)
        if isinstance(decision, PickupRefused):
            raise OrderError(OrderProblem.PICKUP_UNAVAILABLE, pickup_refusal=decision)
        return cls(quote_id, tuple(lines), decision.pickup_at, now, issued_utc + lifetime)

    def recheck(self, *, now: datetime, menu: Menu, policy: PickupPolicy, load: SlotLoad) -> None:
        """Called on EVERY first confirmation, not only when the quote is old.

        The application must call this inside the same storage transaction that reserves
        capacity and saves the order. This domain check alone is NOT a concurrency lock.
        """
        now_utc = aware_utc(now)
        if now_utc < aware_utc(self.issued_at):
            raise ValueError("Confirmation cannot precede the summary")
        if now_utc >= aware_utc(self.expires_at):
            raise OrderError(OrderProblem.EXPIRED_QUOTE)
        for line in self.lines:
            dish = menu.find(line.item_id)
            if dish is None:
                raise OrderError(OrderProblem.UNKNOWN_ITEM)
            if not dish.available:
                raise OrderError(OrderProblem.UNAVAILABLE_ITEM)
            if dish.price != line.unit_price:
                raise OrderError(OrderProblem.PRICE_CHANGED)
        decision = policy.check(self.pickup_at, now=now, items=self.item_count, load=load)
        if isinstance(decision, PickupRefused):
            raise OrderError(OrderProblem.PICKUP_UNAVAILABLE, pickup_refusal=decision)
