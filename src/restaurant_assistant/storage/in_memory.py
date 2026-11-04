"""In-memory repositories for tests and local runs. They implement application/ports.py."""

from restaurant_assistant.domain.menu.menu import Menu


class InMemoryMenuRepository:
    def __init__(self, menu: Menu) -> None:
        self._menu = menu

    def load(self) -> Menu:
        return self._menu
