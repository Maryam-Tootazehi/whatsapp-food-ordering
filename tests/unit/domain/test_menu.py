"""Menu entities and the Menu aggregate (stories M2, M3)."""

from datetime import date

import pytest

from restaurant_assistant.domain.menu.allergen import Allergen, AllergenAnswer, AllergenDeclaration
from restaurant_assistant.domain.menu.menu import Menu, MenuError
from restaurant_assistant.domain.shared.money import Money

from .conftest import item


def test_menu_items_are_equal_by_identity_not_by_values() -> None:
    a = item("margherita", "Margherita", "7.00")
    renamed = item("margherita", "Pizza Margherita", "7.50")
    other = item("bufala", "Margherita", "7.00")
    assert a == renamed
    assert a != other


def test_price_is_money() -> None:
    assert item("margherita", "Margherita", "7.00").price == Money(700)


def test_sold_out_dish_can_be_marked_and_restored() -> None:
    dish = item("diavola", "Diavola", "8.50")
    dish.mark_sold_out()
    assert not dish.available
    dish.mark_available()
    assert dish.available


def test_name_shown_in_the_customers_language() -> None:
    dish = item("acqua", "Acqua naturale", "2.00", name_en="Still water")
    assert dish.display_name("it") == "Acqua naturale"
    assert dish.display_name("en") == "Still water"
    assert item("diavola", "Diavola", "8.50").display_name("en") == "Diavola"


def test_menu_looks_up_by_id(menu: Menu) -> None:
    assert menu.get("capricciosa").name == "Capricciosa"
    assert menu.find("nope") is None
    with pytest.raises(KeyError):
        menu.get("nope")


def test_menu_refuses_duplicate_ids() -> None:
    with pytest.raises(MenuError, match="margherita"):
        Menu([item("margherita", "Margherita", "7"), item("margherita", "Marinara", "6")])


def test_menu_refuses_an_alias_that_points_to_two_dishes() -> None:
    with pytest.raises(MenuError, match="bufala"):
        Menu(
            [
                item("margherita-bufala", "Margherita con bufala", "9", aliases=("bufala",)),
                item("bufala-antipasto", "Mozzarella di bufala", "8", aliases=("Bufala!",)),
            ]
        )


def test_available_items_skip_sold_out(menu: Menu) -> None:
    ids = [dish.id for dish in menu.available_items()]
    assert "diavola" not in ids and "margherita" in ids


# ---- Story M3: allergen answers only from confirmed data ----


def test_confirmed_allergen_is_answered_as_contains(menu: Menu) -> None:
    assert menu.get("margherita").allergen_answer(Allergen.MILK) is AllergenAnswer.CONTAINS


def test_allergen_not_in_a_confirmed_list_is_not_declared_never_safe(menu: Menu) -> None:
    assert menu.get("margherita").allergen_answer(Allergen.FISH) is AllergenAnswer.NOT_DECLARED


def test_unconfirmed_dish_answers_unknown(menu: Menu) -> None:
    assert menu.get("capricciosa").allergen_answer(Allergen.MILK) is AllergenAnswer.UNKNOWN


def test_traces_are_reported_separately() -> None:
    declaration = AllergenDeclaration(
        contains=frozenset({Allergen.GLUTEN}),
        may_contain=frozenset({Allergen.NUTS}),
        confirmed_by="test fixture",
        confirmed_on=date(2026, 11, 4),
    )
    dish = item("pesto", "Pizza al pesto", "9", allergens=declaration)
    assert dish.allergen_answer(Allergen.NUTS) is AllergenAnswer.MAY_CONTAIN


def test_declaration_must_say_who_confirmed_it() -> None:
    with pytest.raises(ValueError):
        AllergenDeclaration(contains=frozenset(), confirmed_by=" ", confirmed_on=date(2026, 11, 4))


def test_there_are_exactly_the_14_eu_allergens_with_italian_names() -> None:
    assert len(Allergen) == 14
    assert Allergen.MILK.italian == "latte"
    assert Allergen.SULPHITES.italian == "anidride solforosa e solfiti"
