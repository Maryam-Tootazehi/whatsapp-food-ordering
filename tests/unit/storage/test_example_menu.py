from restaurant_assistant.application.ports import MenuRepository
from restaurant_assistant.domain.menu.allergen import Allergen, AllergenAnswer
from restaurant_assistant.domain.menu.matching import Matched, MenuMatcher
from restaurant_assistant.storage.example_menu import IS_EXAMPLE_DATA, example_menu
from restaurant_assistant.storage.in_memory import InMemoryMenuRepository


def test_example_menu_is_flagged_as_example_data() -> None:
    assert IS_EXAMPLE_DATA is True


def test_example_menu_respects_the_menu_rules() -> None:
    assert len(example_menu()) > 10  # Menu() would raise on duplicate ids or shared aliases


def test_example_menu_never_claims_confirmed_allergens() -> None:
    assert all(
        dish.allergen_answer(Allergen.MILK) is AllergenAnswer.UNKNOWN for dish in example_menu()
    )


def test_repository_satisfies_the_port_and_feeds_the_matcher() -> None:
    repo: MenuRepository = InMemoryMenuRepository(example_menu())
    # The matcher gets the item text the LLM extracted ("margherite"); quantity ("due") is a
    # separate field of the extraction, so number words are not the matcher's job.
    result = MenuMatcher(repo.load()).match("margherite")
    assert isinstance(result, Matched) and result.item.id == "margherita"
