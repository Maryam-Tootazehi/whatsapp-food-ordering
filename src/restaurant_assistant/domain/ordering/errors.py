"""Machine-readable domain failures. Adapters translate them into customer messages."""

from enum import Enum

from restaurant_assistant.domain.ordering.pickup import PickupRefused


class OrderProblem(Enum):
    EMPTY_ORDER = "empty_order"
    UNKNOWN_ITEM = "unknown_item"
    UNAVAILABLE_ITEM = "unavailable_item"
    PICKUP_UNAVAILABLE = "pickup_unavailable"
    WRONG_QUOTE = "wrong_quote"
    EXPIRED_QUOTE = "expired_quote"
    PRICE_CHANGED = "price_changed"
    INVALID_STATE = "invalid_state"


class OrderError(ValueError):
    def __init__(
        self, problem: OrderProblem, *, pickup_refusal: PickupRefused | None = None
    ) -> None:
        self.problem = problem
        self.pickup_refusal = pickup_refusal
        super().__init__(problem.value)
