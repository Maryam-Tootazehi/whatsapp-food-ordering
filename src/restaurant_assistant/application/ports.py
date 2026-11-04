"""Ports: what the application needs from the outside world, as Protocols.

Adapters in storage/ and interfaces/ implement these. Tests use fakes.
Only the ports the current code needs are here; IntentExtractor (the one LLM call) and
MessagingChannel (WhatsApp / test number) arrive with the pull requests that use them.
"""

from __future__ import annotations

from datetime import datetime
from typing import Protocol

from restaurant_assistant.domain.menu.menu import Menu


class MenuRepository(Protocol):
    def load(self) -> Menu:
        """The current menu, including sold-out flags and confirmed allergen declarations."""
        ...


class Clock(Protocol):
    def now(self) -> datetime:
        """The current time, time-zone aware. Faked in tests so results never depend on the day."""
        ...
