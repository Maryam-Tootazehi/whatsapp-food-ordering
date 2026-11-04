"""Story M2: prices come only from the menu, as integer cents."""

import pytest
from hypothesis import given
from hypothesis import strategies as st

from restaurant_assistant.domain.shared.money import Money

cents = st.integers(min_value=0, max_value=10_000_000)


def test_euros_text_is_stored_as_integer_cents() -> None:
    assert Money.from_euros("8.50") == Money(850)
    assert Money.from_euros("8,50") == Money(850)
    assert Money.from_euros("12") == Money(1200)


def test_rejects_floats_so_rounding_errors_cannot_sneak_in() -> None:
    with pytest.raises(TypeError):
        Money(8.5)  # type: ignore[arg-type]


def test_rejects_more_than_two_decimals() -> None:
    with pytest.raises(ValueError):
        Money.from_euros("8.505")


def test_rejects_negative_amounts() -> None:
    with pytest.raises(ValueError):
        Money(-1)


def test_total_of_two_margherite_and_a_tiramisu() -> None:
    margherita, tiramisu = Money.from_euros("7.00"), Money.from_euros("5.50")
    assert margherita * 2 + tiramisu == Money.from_euros("19.50")


def test_sum_of_nothing_is_zero() -> None:
    assert Money.total([]) == Money.zero()


def test_formats_for_italian_and_english_customers() -> None:
    amount = Money(1950)
    assert amount.format("it") == "19,50 €"
    assert amount.format("en") == "€19.50"
    assert Money(123456).format("it") == "1.234,56 €"
    assert Money(123456).format("en") == "€1,234.56"


def test_cannot_add_different_currencies() -> None:
    with pytest.raises(ValueError):
        Money(100, "EUR") + Money(100, "USD")


@given(cents, cents)
def test_addition_is_commutative(a: int, b: int) -> None:
    assert Money(a) + Money(b) == Money(b) + Money(a)


@given(cents, st.integers(min_value=0, max_value=50))
def test_multiplying_equals_repeated_addition(a: int, n: int) -> None:
    assert Money(a) * n == Money.total([Money(a)] * n)


@given(cents)
def test_formatting_round_trips_through_parsing(a: int) -> None:
    text = Money(a).format("en").removeprefix("€").replace(",", "")
    assert Money.from_euros(text) == Money(a)
