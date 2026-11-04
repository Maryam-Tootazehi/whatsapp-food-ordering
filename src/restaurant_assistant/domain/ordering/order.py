"""PickupOrder aggregate: separate the customer's confirmation from staff acceptance.

This module never saves or sends anything. A draft can be held as conversation state;
only AWAITING_KITCHEN orders may be persisted as placed orders and queued for the kitchen.
The application/storage layer will handle transactions, webhook deduplication and an outbox.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from enum import Enum

from restaurant_assistant.domain.menu.menu import Menu
from restaurant_assistant.domain.ordering.errors import OrderError as OrderError
from restaurant_assistant.domain.ordering.errors import OrderProblem as OrderProblem
from restaurant_assistant.domain.ordering.pickup import PickupPolicy, SlotLoad
from restaurant_assistant.domain.ordering.quote import Quote, aware_utc
from restaurant_assistant.domain.shared.money import Money


class OrderStatus(Enum):
    AWAITING_CUSTOMER = "awaiting_customer"
    AWAITING_KITCHEN = "awaiting_kitchen"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class PickupOrder:
    """Owns all order transitions. No public status setter; failed checks leave it unchanged.

    Ids are supplied by the application, which must make one stable order id per quote.
    This object does not replace a database uniqueness constraint or atomic capacity booking.
    """

    def __init__(self, order_id: str, quote: Quote) -> None:
        if not order_id.strip():
            raise ValueError("An order id is required")
        self._id = order_id
        self._quote = quote
        self._status = OrderStatus.AWAITING_CUSTOMER
        self._confirmed_at: datetime | None = None
        self._decided_by: str | None = None
        self._decided_at: datetime | None = None
        self._rejection_reason: str | None = None

    @property
    def id(self) -> str:
        return self._id

    @property
    def quote(self) -> Quote:
        return self._quote

    @property
    def status(self) -> OrderStatus:
        return self._status

    @property
    def confirmed_at(self) -> datetime | None:
        return self._confirmed_at

    @property
    def decided_by(self) -> str | None:
        return self._decided_by

    @property
    def decided_at(self) -> datetime | None:
        return self._decided_at

    @property
    def rejection_reason(self) -> str | None:
        return self._rejection_reason

    @property
    def total(self) -> Money:
        return self._quote.total

    def confirm(
        self, *, quote_id: str, now: datetime, menu: Menu, policy: PickupPolicy, load: SlotLoad
    ) -> bool:
        """Explicit confirmation of the active quote. True means a new transition occurred.

        A plain yes must be bound to the active quote by conversation code, never by the LLM.
        Interactive replies should carry a quote id. Binding and persistence come next.
        """
        aware_utc(now)
        if quote_id != self._quote.id:
            raise OrderError(OrderProblem.WRONG_QUOTE)
        if self._status in {OrderStatus.AWAITING_KITCHEN, OrderStatus.ACCEPTED}:
            return False  # retry of this quote: don't reserve or send anything twice
        if self._status is not OrderStatus.AWAITING_CUSTOMER:
            raise OrderError(OrderProblem.INVALID_STATE)
        self._quote.recheck(now=now, menu=menu, policy=policy, load=load)
        self._confirmed_at = now
        self._status = OrderStatus.AWAITING_KITCHEN
        return True

    def accept(self, *, staff: str, now: datetime) -> None:
        self._decide(staff=staff, now=now, status=OrderStatus.ACCEPTED)

    def reject(self, *, staff: str, reason: str, now: datetime) -> None:
        if not reason.strip():
            raise ValueError("Staff must give a rejection reason")
        self._decide(staff=staff, now=now, status=OrderStatus.REJECTED)
        self._rejection_reason = reason.strip()

    def _decide(self, *, staff: str, now: datetime, status: OrderStatus) -> None:
        if self._status is not OrderStatus.AWAITING_KITCHEN or self._confirmed_at is None:
            raise OrderError(OrderProblem.INVALID_STATE)
        if not staff.strip():
            raise ValueError("Staff identity is required")
        if aware_utc(now) < aware_utc(self._confirmed_at):
            raise ValueError("Staff decision cannot precede customer confirmation")
        self._decided_by = staff.strip()
        self._decided_at = now
        self._status = status

    def needs_staff_alert(
        self, now: datetime, *, timeout: timedelta = timedelta(minutes=5)
    ) -> bool:
        """Pure overdue detection. A durable worker must later send and deduplicate alerts."""
        now_utc = aware_utc(now)
        if timeout <= timedelta(0):
            raise ValueError("Acceptance timeout must be positive")
        return (
            self._status is OrderStatus.AWAITING_KITCHEN
            and self._confirmed_at is not None
            and now_utc >= aware_utc(self._confirmed_at) + timeout
        )
