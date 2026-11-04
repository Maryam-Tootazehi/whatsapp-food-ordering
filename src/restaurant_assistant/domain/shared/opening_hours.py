"""Opening hours: services (pranzo, cena) per weekday, judged in the restaurant's time zone."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import date, time
from zoneinfo import ZoneInfo

from restaurant_assistant.domain.shared.slot import Slot


@dataclass(frozen=True, slots=True)
class Service:
    """One opening window, e.g. cena 19:00-22:30. Windows past midnight are not supported yet."""

    name: str
    opens: time
    closes: time

    def __post_init__(self) -> None:
        if self.closes <= self.opens:
            raise ValueError(f"{self.name}: must close after it opens")


@dataclass(frozen=True)
class OpeningHours:
    timezone: ZoneInfo
    weekly: Mapping[int, tuple[Service, ...]]  # 0 = Monday ... 6 = Sunday; missing day = closed
    closed_dates: frozenset[date] = field(default_factory=frozenset)

    def services_on(self, day: date) -> tuple[Service, ...]:
        if day in self.closed_dates:
            return ()
        return self.weekly.get(day.weekday(), ())

    def service_for(self, slot: Slot) -> Service | None:
        """The service the whole slot fits into, or None if the restaurant is closed then."""
        start, end = slot.start.astimezone(self.timezone), slot.end.astimezone(self.timezone)
        if start.date() != end.date():  # crosses midnight; no service does that (yet)
            return None
        for service in self.services_on(start.date()):
            if service.opens <= start.time() and end.time() <= service.closes:
                return service
        return None
