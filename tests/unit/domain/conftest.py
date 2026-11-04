"""Test fixtures built directly from domain objects.

These are TEST data, independent of the example menu in storage/, so changing the example menu
(or loading the real one) never breaks domain tests.
"""

from datetime import date

import pytest

from restaurant_assistant.domain.menu.allergen import Allergen, AllergenDeclaration
from restaurant_assistant.domain.menu.menu import Menu
from restaurant_assistant.domain.menu.menu_item import MenuItem
from restaurant_assistant.domain.shared.money import Money

TEST_DECLARATION = AllergenDeclaration(
    contains=frozenset({Allergen.GLUTEN, Allergen.MILK}),
    confirmed_by="test fixture",
    confirmed_on=date(2026, 11, 4),
)


def item(
    item_id: str, name: str, price: str, category: str = "pizze", **kwargs: object
) -> MenuItem:
    return MenuItem(
        id=item_id, name=name, category=category, price=Money.from_euros(price), **kwargs
    )  # type: ignore[arg-type]


@pytest.fixture
def menu() -> Menu:
    return Menu(
        [
            item(
                "margherita", "Margherita", "7.00", aliases=("marghe",), allergens=TEST_DECLARATION
            ),
            item("capricciosa", "Capricciosa", "9.50"),
            item("diavola", "Diavola", "8.50", available=False),
            item("calzone-fritto", "Calzone fritto", "9.00"),
            item("calzone-forno", "Calzone al forno", "9.00"),
            item("tiramisu", "Tiramisù", "5.50", category="dolci", name_en="Tiramisu"),
            item("acqua", "Acqua naturale", "2.00", category="bevande", name_en="Still water"),
        ]
    )
