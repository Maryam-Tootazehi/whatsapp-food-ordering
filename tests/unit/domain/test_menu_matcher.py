"""Story M1: recognise the dish the customer means. One test per acceptance criterion."""

import pytest

from restaurant_assistant.domain.menu.matching import Ambiguous, Matched, MenuMatcher, NotFound
from restaurant_assistant.domain.menu.menu import Menu


@pytest.fixture
def matcher(menu: Menu) -> MenuMatcher:
    return MenuMatcher(menu)


@pytest.mark.parametrize("typed", ["margherita", "Margherita!", "MARGHERITA", "  margherita "])
def test_matches_regardless_of_case_and_punctuation(matcher: MenuMatcher, typed: str) -> None:
    result = matcher.match(typed)
    assert isinstance(result, Matched) and result.item.id == "margherita"
    assert result.how == "exact"


def test_ignores_accents(matcher: MenuMatcher) -> None:
    result = matcher.match("tiramisu")
    assert isinstance(result, Matched) and result.item.id == "tiramisu"


@pytest.mark.parametrize(
    ("typed", "expected"), [("margherite", "margherita"), ("calzoni fritti", "calzone-fritto")]
)
def test_understands_italian_plurals(matcher: MenuMatcher, typed: str, expected: str) -> None:
    result = matcher.match(typed)
    assert isinstance(result, Matched) and result.item.id == expected


def test_matches_owner_approved_alias(matcher: MenuMatcher) -> None:
    result = matcher.match("marghe")
    assert isinstance(result, Matched) and result.item.id == "margherita"
    assert result.how == "alias"


def test_matches_the_english_name(matcher: MenuMatcher) -> None:
    result = matcher.match("still water")
    assert isinstance(result, Matched) and result.item.id == "acqua"


def test_tolerates_a_small_typo(matcher: MenuMatcher) -> None:
    result = matcher.match("capriciosa")
    assert isinstance(result, Matched) and result.item.id == "capricciosa"
    assert result.how == "fuzzy"


def test_partial_name_that_fits_two_dishes_is_ambiguous(matcher: MenuMatcher) -> None:
    result = matcher.match("calzone")
    assert isinstance(result, Ambiguous)
    assert {c.id for c in result.candidates} == {"calzone-fritto", "calzone-forno"}


def test_partial_name_that_fits_one_dish_matches(matcher: MenuMatcher) -> None:
    result = matcher.match("calzone fritto")
    assert isinstance(result, Matched) and result.item.id == "calzone-fritto"
    result = matcher.match("fritto")
    assert isinstance(result, Matched) and result.item.id == "calzone-fritto"
    assert result.how == "partial"


def test_filler_words_are_ignored(matcher: MenuMatcher) -> None:
    result = matcher.match("una pizza margherita per favore")
    assert isinstance(result, Matched) and result.item.id == "margherita"


@pytest.mark.parametrize("typed", ["sushi", "", "!!!", "pizza"])
def test_nothing_is_guessed_when_nothing_fits(matcher: MenuMatcher, typed: str) -> None:
    assert isinstance(matcher.match(typed), NotFound)


def test_sold_out_dish_still_matches_so_we_can_say_it_is_sold_out(matcher: MenuMatcher) -> None:
    result = matcher.match("diavola")
    assert isinstance(result, Matched) and result.item.id == "diavola"
    assert not result.item.available
