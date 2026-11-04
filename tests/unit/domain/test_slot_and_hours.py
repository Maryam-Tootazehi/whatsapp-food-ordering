"""Slot and OpeningHours value objects (shared kernel)."""

from datetime import UTC, date, datetime, time
from zoneinfo import ZoneInfo

import pytest

from restaurant_assistant.domain.shared.opening_hours import OpeningHours, Service
from restaurant_assistant.domain.shared.slot import Slot

ROME = ZoneInfo("Europe/Rome")
FRIDAY = date(2026, 11, 6)
MONDAY = date(2026, 11, 9)


def at(day: date, hh: int, mm: int = 0) -> datetime:
    return datetime.combine(day, time(hh, mm), tzinfo=ROME)


@pytest.fixture
def hours() -> OpeningHours:
    lunch, dinner = (
        Service("pranzo", time(12, 0), time(14, 30)),
        Service("cena", time(19, 0), time(22, 30)),
    )
    return OpeningHours(
        timezone=ROME,
        weekly={day: (lunch, dinner) for day in range(1, 7)},  # Tuesday..Sunday; Monday (0) closed
        closed_dates=frozenset({date(2026, 12, 25)}),
    )


def test_a_time_falls_into_its_quarter_hour_slot() -> None:
    slot = Slot.containing(at(FRIDAY, 20, 7))
    assert slot.start == at(FRIDAY, 20, 0) and slot.end == at(FRIDAY, 20, 15)
    assert slot.label() == "20:00"


def test_next_slot_follows_directly() -> None:
    assert Slot.containing(at(FRIDAY, 20, 7)).next() == Slot.containing(at(FRIDAY, 20, 15))


def test_slot_needs_a_time_zone() -> None:
    with pytest.raises(ValueError):
        Slot.containing(datetime(2026, 11, 6, 20, 0))


def test_slot_must_end_after_it_starts() -> None:
    with pytest.raises(ValueError):
        Slot(at(FRIDAY, 20), at(FRIDAY, 20))


def test_slots_are_value_objects() -> None:
    assert Slot.containing(at(FRIDAY, 20, 1)) == Slot.containing(at(FRIDAY, 20, 14))


def test_open_during_dinner(hours: OpeningHours) -> None:
    service = hours.service_for(Slot.containing(at(FRIDAY, 20)))
    assert service is not None and service.name == "cena"


def test_last_slot_of_the_service_is_open_but_not_after(hours: OpeningHours) -> None:
    assert hours.service_for(Slot.containing(at(FRIDAY, 22, 15))) is not None
    assert hours.service_for(Slot.containing(at(FRIDAY, 22, 30))) is None


def test_closed_between_services_on_mondays_and_holidays(hours: OpeningHours) -> None:
    assert hours.service_for(Slot.containing(at(FRIDAY, 16))) is None
    assert hours.service_for(Slot.containing(at(MONDAY, 20))) is None
    assert hours.service_for(Slot.containing(at(date(2026, 12, 25), 20))) is None


def test_times_in_other_zones_are_judged_in_restaurant_time(hours: OpeningHours) -> None:
    # 19:00 UTC on a November Friday is 20:00 in Rome (UTC+1).
    utc_slot = Slot.containing(datetime(2026, 11, 6, 19, 0, tzinfo=UTC))
    assert hours.service_for(utc_slot) is not None


def test_service_must_close_after_it_opens() -> None:
    with pytest.raises(ValueError):
        Service("cena", time(22, 0), time(19, 0))
