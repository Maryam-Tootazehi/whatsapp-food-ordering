"""
######################################################################################
#  EXAMPLE DATA. NOT THE RESTAURANT'S MENU.                                          #
#  Invented dishes and prices for development until the owner meeting. Replace with  #
#  the owner-confirmed menu before any real customer uses the assistant.             #
#                                                                                    #
#  Allergens are deliberately left unconfirmed (None) on every dish: we never invent #
#  allergen data, not even as an example. The assistant will answer "unknown" and    #
#  hand over to staff, which is the correct behaviour for unconfirmed data.          #
######################################################################################
"""

from restaurant_assistant.domain.menu.menu import Menu
from restaurant_assistant.domain.menu.menu_item import MenuItem
from restaurant_assistant.domain.shared.money import Money

IS_EXAMPLE_DATA = True


def _dish(
    item_id: str,
    name: str,
    category: str,
    euros: str,
    name_en: str | None = None,
    aliases: tuple[str, ...] = (),
) -> MenuItem:
    return MenuItem(
        id=item_id,
        name=name,
        category=category,
        price=Money.from_euros(euros),
        name_en=name_en,
        aliases=aliases,
    )


def example_menu() -> Menu:
    return Menu(
        [
            _dish(
                "bruschetta",
                "Bruschetta al pomodoro",
                "antipasti",
                "5.00",
                name_en="Tomato bruschetta",
            ),
            _dish("supplì", "Supplì", "antipasti", "2.50", name_en="Rice croquette"),
            _dish("margherita", "Margherita", "pizze", "7.00", aliases=("marghe",)),
            _dish("marinara", "Marinara", "pizze", "6.00"),
            _dish("diavola", "Diavola", "pizze", "8.50", name_en="Spicy salami pizza"),
            _dish("capricciosa", "Capricciosa", "pizze", "9.50"),
            _dish(
                "quattro-formaggi",
                "Quattro formaggi",
                "pizze",
                "9.00",
                aliases=("4 formaggi",),
                name_en="Four cheese",
            ),
            _dish("calzone-fritto", "Calzone fritto", "pizze", "9.00", name_en="Fried calzone"),
            _dish("calzone-forno", "Calzone al forno", "pizze", "9.00", name_en="Baked calzone"),
            _dish(
                "carbonara", "Spaghetti alla carbonara", "primi", "11.00", aliases=("carbonara",)
            ),
            _dish("tiramisu", "Tiramisù", "dolci", "5.50", name_en="Tiramisu"),
            _dish("panna-cotta", "Panna cotta", "dolci", "5.00"),
            _dish(
                "acqua",
                "Acqua naturale 0,5 l",
                "bevande",
                "2.00",
                aliases=("acqua",),
                name_en="Still water",
            ),
            _dish("coca-cola", "Coca-Cola 33 cl", "bevande", "3.00", aliases=("coca cola", "coca")),
        ]
    )
