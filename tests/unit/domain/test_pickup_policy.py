"""Story O1: check the pickup time. One test per acceptance criterion."""

from collections.abc import Mapping
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

import pytest

from restaurant_assistant.domain.kitchen.capacity import KitchenCapacity
from restaurant_assistant.domain.ordering.pickup import (
    PickupAccepted,
    PickupPolicy,
    PickupRefused,
    Refusal,
)
from restaurant_assistant.domain.shared.opening_hours import OpeningHours, Service
from restaurant_assistant.domain.shared.slot import Slot

ROME = ZoneInfo("Europe/Rome")
FRIDAY = date(2026, 11, 6)
SATURDAY = date(2026, 11, 7)
MONDAY = date(2026, 11, 9)


def at(day: date, hh: int, mm: int = 0) -> datetime:
    return datetime.combine(day, time(hh, mm), tzinfo=ROME)


def no_load(slot: Slot) -> int:
    return 0


def load_from(booked: Mapping[datetime, int]):  # type: ignore[no-untyped-def]
    return lambda slot: booked.get(slot.start, 0)


@pytest.fixture
def policy() -> PickupPolicy:
    lunch, dinner = (
        Service("pranzo", time(12, 0), time(14, 30)),
        Service("cena", time(19, 0), time(22, 30)),
    )
    hours = OpeningHours(timezone=ROME, weekly={d: (lunch, dinner) for d in range(1, 7)})
    return PickupPolicy(
        hours, KitchenCapacity(max_items_per_slot=10), lead_time=timedelta(minutes=20)
    )


def test_accepts_an_open_slot_with_room(policy: PickupPolicy) -> None:
    decision = policy.check(at(FRIDAY, 20), now=at(FRIDAY, 18), items=2, load=no_load)
    assert isinstance(decision, PickupAccepted)
    assert decision.slot == Slot.containing(at(FRIDAY, 20))
    assert decision.pickup_at == at(FRIDAY, 20)


def test_time_like_20_07_uses_the_20_00_slot(policy: PickupPolicy) -> None:
    decision = policy.check(at(FRIDAY, 20, 7), now=at(FRIDAY, 18), items=1, load=no_load)
    assert isinstance(decision, PickupAccepted) and decision.slot.label() == "20:00"


def test_refuses_after_closing(policy: PickupPolicy) -> None:
    decision = policy.check(at(FRIDAY, 23), now=at(FRIDAY, 18), items=1, load=no_load)
    assert isinstance(decision, PickupRefused) and decision.reason is Refusal.CLOSED


def test_refuses_on_the_weekly_closing_day(policy: PickupPolicy) -> None:
    decision = policy.check(at(MONDAY, 20), now=at(FRIDAY, 18), items=1, load=no_load)
    assert isinstance(decision, PickupRefused) and decision.reason is Refusal.CLOSED


def test_refuses_inside_the_lead_time(policy: PickupPolicy) -> None:
    decision = policy.check(at(FRIDAY, 20), now=at(FRIDAY, 19, 50), items=1, load=no_load)
    assert isinstance(decision, PickupRefused) and decision.reason is Refusal.TOO_SOON


def test_refuses_a_time_in_the_past(policy: PickupPolicy) -> None:
    decision = policy.check(at(FRIDAY, 19), now=at(FRIDAY, 20), items=1, load=no_load)
    assert isinstance(decision, PickupRefused) and decision.reason is Refusal.IN_THE_PAST


def test_refuses_when_the_kitchen_is_full(policy: PickupPolicy) -> None:
    booked = load_from({at(FRIDAY, 20): 8})
    decision = policy.check(at(FRIDAY, 20), now=at(FRIDAY, 18), items=3, load=booked)
    assert isinstance(decision, PickupRefused) and decision.reason is Refusal.KITCHEN_FULL


def test_exactly_full_is_still_accepted(policy: PickupPolicy) -> None:
    booked = load_from({at(FRIDAY, 20): 8})
    decision = policy.check(at(FRIDAY, 20), now=at(FRIDAY, 18), items=2, load=booked)
    assert isinstance(decision, PickupAccepted)


def test_suggests_the_next_slots_with_room(policy: PickupPolicy) -> None:
    booked = load_from({at(FRIDAY, 20): 10, at(FRIDAY, 20, 15): 9})
    decision = policy.check(at(FRIDAY, 20), now=at(FRIDAY, 18), items=2, load=booked)
    assert isinstance(decision, PickupRefused)
    assert [s.label() for s in decision.alternatives] == ["20:30", "20:45", "21:00"]


def test_after_closing_suggests_the_next_service(policy: PickupPolicy) -> None:
    decision = policy.check(at(FRIDAY, 23), now=at(FRIDAY, 22, 50), items=1, load=no_load)
    assert isinstance(decision, PickupRefused)
    assert decision.alternatives[0].start == at(SATURDAY, 12, 0)


def test_too_soon_suggests_the_first_slot_after_the_lead_time(policy: PickupPolicy) -> None:
    decision = policy.check(at(FRIDAY, 20), now=at(FRIDAY, 19, 50), items=1, load=no_load)
    assert isinstance(decision, PickupRefused)
    assert decision.alternatives[0].label() == "20:15"


def test_order_bigger_than_a_whole_slot_goes_to_staff(policy: PickupPolicy) -> None:
    decision = policy.check(at(FRIDAY, 20), now=at(FRIDAY, 18), items=11, load=no_load)
    assert isinstance(decision, PickupRefused)
    assert decision.reason is Refusal.TOO_LARGE and decision.alternatives == ()


def test_needs_at_least_one_item(policy: PickupPolicy) -> None:
    with pytest.raises(ValueError):
        policy.check(at(FRIDAY, 20), now=at(FRIDAY, 18), items=0, load=no_load)
