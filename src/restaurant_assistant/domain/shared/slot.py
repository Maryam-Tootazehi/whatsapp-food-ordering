"""Slot value object: a time interval such as 20:00-20:15 (fascia oraria)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

DEFAULT_MINUTES = 15


def _require_aware(moment: datetime) -> None:
    if moment.tzinfo is None or moment.utcoffset() is None:
        raise ValueError(f"Times must carry a time zone, got {moment!r}")


@dataclass(frozen=True, slots=True, order=True)
class Slot:
    start: datetime
    end: datetime

    def __post_init__(self) -> None:
        _require_aware(self.start)
        _require_aware(self.end)
        if self.end <= self.start:
            raise ValueError("A slot must end after it starts")

    @classmethod
    def containing(cls, moment: datetime, minutes: int = DEFAULT_MINUTES) -> Slot:
        """The slot a moment falls into: 20:07 -> 20:00-20:15 (in the moment's own time zone)."""
        _require_aware(moment)
        if minutes <= 0 or 60 % minutes:
            raise ValueError("Slot length must divide an hour (5, 10, 15, 20, 30, 60)")
        start = moment.replace(
            minute=moment.minute - moment.minute % minutes, second=0, microsecond=0
        )
        return cls(start, start + timedelta(minutes=minutes))

    @property
    def length(self) -> timedelta:
        return self.end - self.start

    def next(self) -> Slot:
        return Slot(self.end, self.end + self.length)

    def label(self) -> str:
        return self.start.strftime("%H:%M")
