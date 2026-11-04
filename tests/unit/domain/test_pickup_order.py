"""O2/O3: a summary is not a placed order; customer and kitchen confirmations differ.

All data and times are fixtures. No WhatsApp, model, database or real clock is used.
"""

from dataclasses import FrozenInstanceError
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

import pytest

from restaurant_assistant.domain.kitchen.capacity import KitchenCapacity
from restaurant_assistant.domain.menu.menu import Menu
from restaurant_assistant.domain.ordering.order import (
    OrderError,
    OrderProblem,
    OrderStatus,
    PickupOrder,
)
from restaurant_assistant.domain.ordering.pickup import PickupPolicy
from restaurant_assistant.domain.ordering.quote import OrderLine, Quote, RequestedItem
from restaurant_assistant.domain.shared.money import Money
from restaurant_assistant.domain.shared.opening_hours import OpeningHours, Service
from restaurant_assistant.domain.shared.slot import Slot

ROME = ZoneInfo("Europe/Rome")
NOW = datetime(2026, 11, 6, 18, 0, tzinfo=ROME)
PICKUP = NOW.replace(hour=20)


def empty_kitchen(slot: Slot) -> int:
    return 0


@pytest.fixture
def policy() -> PickupPolicy:
    return PickupPolicy(
        OpeningHours(ROME, {4: (Service("cena", time(19), time(22, 30)),)}),
        KitchenCapacity(10),
    )


def make_quote(menu: Menu, policy: PickupPolicy, **overrides: object) -> Quote:
    args = dict(
        quote_id="quote-1",
        requested=(RequestedItem("margherita", 2), RequestedItem("tiramisu", 1)),
        menu=menu,
        pickup_at=PICKUP,
        now=NOW,
        policy=policy,
        load=empty_kitchen,
    )
    args.update(overrides)
    return Quote.build(**args)  # type: ignore[arg-type]


@pytest.fixture
def quote(menu: Menu, policy: PickupPolicy) -> Quote:
    return make_quote(menu, policy)


@pytest.fixture
def order(quote: Quote) -> PickupOrder:
    return PickupOrder("order-1", quote)


def confirm(order: PickupOrder, menu: Menu, policy: PickupPolicy, **overrides: object) -> bool:
    args = dict(
        quote_id="quote-1",
        now=NOW + timedelta(minutes=1),
        menu=menu,
        policy=policy,
        load=empty_kitchen,
    )
    args.update(overrides)
    return order.confirm(**args)  # type: ignore[arg-type]


def test_summary_uses_menu_prices_not_customer_or_model_prices(quote: Quote) -> None:
    assert quote.total == Money(1950)
    assert quote.lines[0] == OrderLine("margherita", "Margherita", 2, Money(700))
    assert quote.pickup_at == PICKUP
    assert quote.expires_at == NOW + timedelta(minutes=10)


def test_summary_and_lines_are_immutable_snapshots(quote: Quote, menu: Menu) -> None:
    menu.get("margherita").price = Money(900)
    menu.get("margherita").name = "New name"
    assert quote.lines[0].unit_price == Money(700)
    assert quote.lines[0].name == "Margherita"
    with pytest.raises(FrozenInstanceError):
        quote.lines[0].quantity = 9  # type: ignore[misc]


def test_repeated_dish_lines_are_combined(menu: Menu, policy: PickupPolicy) -> None:
    q = make_quote(
        menu, policy, requested=(RequestedItem("margherita", 1), RequestedItem("margherita", 2))
    )
    assert len(q.lines) == 1 and q.lines[0].quantity == 3 and q.total == Money(2100)


@pytest.mark.parametrize("quantity", [0, -1, True, 1.5])
def test_quantity_must_be_a_positive_whole_number(quantity: object) -> None:
    with pytest.raises(ValueError):
        RequestedItem("margherita", quantity)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "requested,problem",
    [
        ((), OrderProblem.EMPTY_ORDER),
        ((RequestedItem("sushi", 1),), OrderProblem.UNKNOWN_ITEM),
        ((RequestedItem("diavola", 1),), OrderProblem.UNAVAILABLE_ITEM),
    ],
)
def test_invalid_requests_do_not_become_quotes(
    menu: Menu, policy: PickupPolicy, requested: tuple[RequestedItem, ...], problem: OrderProblem
) -> None:
    with pytest.raises(OrderError) as exc:
        make_quote(menu, policy, requested=requested)
    assert exc.value.problem is problem


def test_closed_pickup_does_not_become_a_quote(menu: Menu, policy: PickupPolicy) -> None:
    with pytest.raises(OrderError) as exc:
        make_quote(menu, policy, pickup_at=PICKUP.replace(hour=23))
    assert exc.value.problem is OrderProblem.PICKUP_UNAVAILABLE
    assert exc.value.pickup_refusal is not None


def test_a_quote_is_not_yet_a_confirmed_order(order: PickupOrder) -> None:
    assert order.status is OrderStatus.AWAITING_CUSTOMER
    assert order.confirmed_at is None
    assert order.needs_staff_alert(NOW + timedelta(hours=1)) is False


def test_customer_confirmation_still_waits_for_kitchen(
    order: PickupOrder, menu: Menu, policy: PickupPolicy
) -> None:
    assert confirm(order, menu, policy) is True
    assert order.status is OrderStatus.AWAITING_KITCHEN
    assert order.confirmed_at == NOW + timedelta(minutes=1)
    assert order.total == Money(1950)


def test_confirmation_for_the_wrong_summary_is_rejected(
    order: PickupOrder, menu: Menu, policy: PickupPolicy
) -> None:
    with pytest.raises(OrderError) as exc:
        confirm(order, menu, policy, quote_id="an-older-summary")
    assert exc.value.problem is OrderProblem.WRONG_QUOTE
    assert order.status is OrderStatus.AWAITING_CUSTOMER


@pytest.mark.parametrize("minutes", [10, 11])
def test_expired_summary_needs_a_new_summary(
    order: PickupOrder, menu: Menu, policy: PickupPolicy, minutes: int
) -> None:
    with pytest.raises(OrderError) as exc:
        confirm(order, menu, policy, now=NOW + timedelta(minutes=minutes))
    assert exc.value.problem is OrderProblem.EXPIRED_QUOTE
    assert order.status is OrderStatus.AWAITING_CUSTOMER


def test_price_change_needs_a_new_summary(
    order: PickupOrder, menu: Menu, policy: PickupPolicy
) -> None:
    menu.get("margherita").price = Money(750)
    with pytest.raises(OrderError) as exc:
        confirm(order, menu, policy)
    assert exc.value.problem is OrderProblem.PRICE_CHANGED
    assert order.status is OrderStatus.AWAITING_CUSTOMER and order.total == Money(1950)


def test_sold_out_after_summary_cannot_be_confirmed(
    order: PickupOrder, menu: Menu, policy: PickupPolicy
) -> None:
    menu.get("margherita").mark_sold_out()
    with pytest.raises(OrderError) as exc:
        confirm(order, menu, policy)
    assert exc.value.problem is OrderProblem.UNAVAILABLE_ITEM
    assert order.status is OrderStatus.AWAITING_CUSTOMER


def test_removed_dish_cannot_be_confirmed(
    order: PickupOrder, menu: Menu, policy: PickupPolicy
) -> None:
    current = Menu([dish for dish in menu if dish.id != "tiramisu"])
    with pytest.raises(OrderError) as exc:
        confirm(order, current, policy)
    assert exc.value.problem is OrderProblem.UNKNOWN_ITEM


def test_capacity_is_checked_again_even_one_minute_later(
    order: PickupOrder, menu: Menu, policy: PickupPolicy
) -> None:
    with pytest.raises(OrderError) as exc:
        confirm(order, menu, policy, load=lambda slot: 8)
    assert exc.value.problem is OrderProblem.PICKUP_UNAVAILABLE
    assert order.status is OrderStatus.AWAITING_CUSTOMER


def test_later_confirmation_cannot_ignore_preparation_time(
    order: PickupOrder, menu: Menu, quote: Quote
) -> None:
    slower_kitchen = PickupPolicy(
        OpeningHours(ROME, {4: (Service("cena", time(19), time(22, 30)),)}),
        KitchenCapacity(10),
        lead_time=timedelta(hours=3),
    )
    with pytest.raises(OrderError) as exc:
        confirm(order, menu, slower_kitchen)
    assert exc.value.problem is OrderProblem.PICKUP_UNAVAILABLE


def test_duplicate_yes_does_not_confirm_twice_or_recheck_its_own_load(
    order: PickupOrder, menu: Menu, policy: PickupPolicy
) -> None:
    confirm(order, menu, policy)
    assert (
        confirm(order, menu, policy, now=NOW + timedelta(minutes=30), load=lambda slot: 10) is False
    )
    assert order.confirmed_at == NOW + timedelta(minutes=1)


def test_staff_can_accept_only_after_customer_confirmation(order: PickupOrder) -> None:
    with pytest.raises(OrderError) as exc:
        order.accept(staff="Owner", now=NOW + timedelta(minutes=2))
    assert exc.value.problem is OrderProblem.INVALID_STATE


def test_kitchen_acceptance_records_who_and_when(
    order: PickupOrder, menu: Menu, policy: PickupPolicy
) -> None:
    confirm(order, menu, policy)
    order.accept(staff="Owner", now=NOW + timedelta(minutes=2))
    assert order.status is OrderStatus.ACCEPTED
    assert order.decided_by == "Owner" and order.decided_at == NOW + timedelta(minutes=2)
    assert order.needs_staff_alert(NOW + timedelta(minutes=20)) is False


def test_kitchen_rejection_requires_a_reason(
    order: PickupOrder, menu: Menu, policy: PickupPolicy
) -> None:
    confirm(order, menu, policy)
    with pytest.raises(ValueError):
        order.reject(staff="Owner", reason=" ", now=NOW + timedelta(minutes=2))
    assert order.status is OrderStatus.AWAITING_KITCHEN
    order.reject(staff="Owner", reason="Oven broken", now=NOW + timedelta(minutes=2))
    assert order.status is OrderStatus.REJECTED and order.rejection_reason == "Oven broken"
    assert order.needs_staff_alert(NOW + timedelta(minutes=20)) is False


def test_staff_cannot_reverse_an_accepted_order(
    order: PickupOrder, menu: Menu, policy: PickupPolicy
) -> None:
    confirm(order, menu, policy)
    order.accept(staff="Owner", now=NOW + timedelta(minutes=2))
    with pytest.raises(OrderError):
        order.reject(staff="Owner", reason="Changed my mind", now=NOW + timedelta(minutes=3))
    assert order.status is OrderStatus.ACCEPTED


def test_rejected_order_cannot_be_revived_by_another_yes(
    order: PickupOrder, menu: Menu, policy: PickupPolicy
) -> None:
    confirm(order, menu, policy)
    order.reject(staff="Owner", reason="Oven broken", now=NOW + timedelta(minutes=2))
    with pytest.raises(OrderError) as exc:
        confirm(order, menu, policy)
    assert exc.value.problem is OrderProblem.INVALID_STATE


def test_alert_becomes_due_exactly_five_minutes_after_confirmation(
    order: PickupOrder, menu: Menu, policy: PickupPolicy
) -> None:
    confirm(order, menu, policy)
    assert not order.needs_staff_alert(NOW + timedelta(minutes=5, seconds=59))
    assert order.needs_staff_alert(NOW + timedelta(minutes=6))


def test_naive_customer_timestamp_is_rejected(
    order: PickupOrder, menu: Menu, policy: PickupPolicy
) -> None:
    with pytest.raises(ValueError):
        confirm(order, menu, policy, now=NOW.replace(tzinfo=None))
    assert order.status is OrderStatus.AWAITING_CUSTOMER


def test_confirmation_cannot_happen_before_quote(
    order: PickupOrder, menu: Menu, policy: PickupPolicy
) -> None:
    with pytest.raises(ValueError):
        confirm(order, menu, policy, now=NOW - timedelta(seconds=1))


def test_staff_timestamp_cannot_precede_confirmation(
    order: PickupOrder, menu: Menu, policy: PickupPolicy
) -> None:
    confirm(order, menu, policy)
    with pytest.raises(ValueError):
        order.accept(staff="Owner", now=NOW)
    assert order.status is OrderStatus.AWAITING_KITCHEN


def test_staff_name_is_required(order: PickupOrder, menu: Menu, policy: PickupPolicy) -> None:
    confirm(order, menu, policy)
    with pytest.raises(ValueError):
        order.accept(staff=" ", now=NOW + timedelta(minutes=2))


@pytest.mark.parametrize(
    "change",
    [
        {"quote_id": " "},
        {"lifetime": timedelta(0)},
        {"now": NOW.replace(tzinfo=None)},
        {"pickup_at": PICKUP.replace(tzinfo=None)},
    ],
)
def test_invalid_quote_metadata_is_rejected(
    menu: Menu, policy: PickupPolicy, change: dict[str, object]
) -> None:
    with pytest.raises(ValueError):
        make_quote(menu, policy, **change)


@pytest.mark.parametrize(
    "item_id,name,currency",
    [
        ("", "Margherita", "EUR"),
        ("margherita", " ", "EUR"),
        ("margherita", "Margherita", "USD"),
    ],
)
def test_invalid_line_snapshots_are_rejected(item_id: str, name: str, currency: str) -> None:
    with pytest.raises(ValueError):
        OrderLine(item_id, name, 1, Money(700, currency))


def test_blank_request_id_is_rejected() -> None:
    with pytest.raises(ValueError):
        RequestedItem(" ", 1)


def test_cannot_construct_a_quote_with_mutable_lines(quote: Quote) -> None:
    with pytest.raises(ValueError):
        Quote(quote.id, list(quote.lines), PICKUP, NOW, quote.expires_at)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "change",
    [
        {"lines": ()},
        {"expires_at": NOW},
        {"pickup_at": NOW},
    ],
)
def test_direct_quote_construction_protects_invariants(
    quote: Quote, change: dict[str, object]
) -> None:
    args = dict(
        id=quote.id, lines=quote.lines, pickup_at=PICKUP, issued_at=NOW, expires_at=quote.expires_at
    )
    args.update(change)
    with pytest.raises(ValueError):
        Quote(**args)  # type: ignore[arg-type]


def test_direct_quote_construction_rejects_duplicate_lines(quote: Quote) -> None:
    with pytest.raises(ValueError):
        Quote(quote.id, (quote.lines[0], quote.lines[0]), PICKUP, NOW, quote.expires_at)


def test_an_order_needs_a_stable_id(quote: Quote) -> None:
    with pytest.raises(ValueError):
        PickupOrder(" ", quote)


def test_duplicate_yes_after_staff_acceptance_is_a_no_op(
    order: PickupOrder, menu: Menu, policy: PickupPolicy
) -> None:
    confirm(order, menu, policy)
    order.accept(staff="Owner", now=NOW + timedelta(minutes=2))
    assert confirm(order, menu, policy) is False
    assert order.status is OrderStatus.ACCEPTED
    assert order.id == "order-1" and order.quote.id == "quote-1"


def test_staff_alert_timeout_must_be_positive(order: PickupOrder) -> None:
    with pytest.raises(ValueError):
        order.needs_staff_alert(NOW, timeout=timedelta(0))


def test_expiry_uses_elapsed_time_when_clocks_go_back(menu: Menu) -> None:
    # Italy changes from 03:00 to 02:00 on 25 October 2026.
    # 02:55 summer time -> 02:05 winter time is TEN minutes later, not fifty minutes earlier.
    issued = datetime(2026, 10, 25, 2, 55, tzinfo=ROME, fold=0)
    expires = datetime(2026, 10, 25, 2, 5, tzinfo=ROME, fold=1)
    pickup = datetime(2026, 10, 25, 4, 0, tzinfo=ROME)
    q = Quote(
        "dst-quote",
        (OrderLine("margherita", "Margherita", 1, Money(700)),),
        pickup,
        issued,
        expires,
    )
    policy = PickupPolicy(
        OpeningHours(ROME, {6: (Service("test", time(0), time(23, 59)),)}),
        KitchenCapacity(10),
        lead_time=timedelta(0),
    )
    with pytest.raises(OrderError) as exc:
        q.recheck(now=expires, menu=menu, policy=policy, load=empty_kitchen)
    assert exc.value.problem is OrderProblem.EXPIRED_QUOTE
