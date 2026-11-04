"""Offline walkthrough with example data and a fixed clock, NOT a live ordering interface.

Run: poetry run python -m restaurant_assistant.interfaces.demo_order
"""

from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from restaurant_assistant.domain.kitchen.capacity import KitchenCapacity
from restaurant_assistant.domain.ordering.order import PickupOrder
from restaurant_assistant.domain.ordering.pickup import PickupPolicy
from restaurant_assistant.domain.ordering.quote import Quote, RequestedItem
from restaurant_assistant.domain.shared.opening_hours import OpeningHours, Service
from restaurant_assistant.storage.example_menu import example_menu


def main() -> None:
    print("EXAMPLE ONLY: invented menu, hours, capacity and a fixed test clock.")
    now = datetime(2026, 11, 6, 18, 0, tzinfo=ZoneInfo("Europe/Rome"))
    menu = example_menu()
    policy = PickupPolicy(
        OpeningHours(ZoneInfo("Europe/Rome"), {4: (Service("cena", time(19), time(22, 30)),)}),
        KitchenCapacity(10),
    )
    # Item ids are already resolved. No LLM is needed for this domain walkthrough.
    quote = Quote.build(
        quote_id="demo-quote",
        requested=(RequestedItem("margherita", 2), RequestedItem("tiramisu", 1)),
        menu=menu,
        pickup_at=now.replace(hour=20),
        now=now,
        policy=policy,
        load=lambda slot: 0,
    )
    order = PickupOrder("demo-order", quote)
    print("1. Customer asks for two Margherita pizzas and one tiramisu for 20:00.")
    print(f"2. Code reads menu prices: {quote.total.format('it')}.")
    print(f"3. Summary shown, NOT yet placed: {order.status.value}.")
    order.confirm(
        quote_id=quote.id,
        now=now + timedelta(minutes=1),
        menu=menu,
        policy=policy,
        load=lambda slot: 0,
    )
    print(f"4. Customer confirms; fresh checks pass: {order.status.value}.")
    print("   Customer message: request received, waiting for the restaurant to accept.")
    order.accept(staff="Example owner", now=now + timedelta(minutes=2))
    print(f"5. Staff accept: {order.status.value}.")
    print("No messages sent. No database writes.")


if __name__ == "__main__":
    main()
