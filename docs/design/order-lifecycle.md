# An order is not a promise until the restaurant accepts it

## The simple version

A quote is a shopping basket: dishes, quantities, prices and a pickup time. Showing it is not
placing an order. The customer must confirm that exact basket. Then staff must accept it.

```
Quote -> awaiting_customer -> awaiting_kitchen -> accepted
                                             -> rejected
```

The state machine deliberately does not yet model paid, prepared, collected, cancelled or
refunded. The owner's interview must establish those rules first.

## What this step implements

- `RequestedItem`: an already matched menu id and a positive whole quantity. No model price input.
- `OrderLine`: an immutable name, unit price and quantity snapshot. Editing the menu cannot
  silently rewrite the summary the customer saw.
- `Quote`: combines repeated items, checks availability and pickup feasibility, and computes
  the total from menu prices. The provisional lifetime is ten elapsed minutes, configurable.
- `PickupOrder`: the aggregate owns state changes. Its status cannot be assigned publicly.
- Confirmation must name the active quote id. A different quote id is rejected.
- EVERY first confirmation rechecks the menu, price, availability, preparation time and capacity.
  A changed price needs a fresh summary and new consent, not a silent price change.
- Repeating confirmation on the same object after confirmation/acceptance is a no-op. It must
  not reserve capacity twice. A rejected order cannot be revived by another yes.
- Staff acceptance and rejection require an identity and timestamp. Rejection needs a reason.
- `needs_staff_alert()` detects a pending order at five elapsed minutes; it does NOT send alerts.
- Every time has a time zone. Quote expiry and overdue checks use UTC for elapsed time,
  so daylight saving changes do not stretch or shorten the deadline.

For the interview: **the aggregate is the gatekeeper**. Outside code asks it to confirm or
accept an order; it cannot skip straight to a new status without checking the rules.

## What must come next before real customers

This code is pure domain logic. It does not save orders, reserve capacity, receive WhatsApp,
interpret typed yes/no, generate ids, send kitchen tickets or alert the owner.

The application and storage adapters must:

1. Bind a customer's explicit action to their OWN active quote. Use a quote-bound interactive
   confirmation when possible. A bare yes belongs only to the active pending summary; do not
   let the LLM turn unrelated text into consent. An old button cannot confirm a new basket.
2. Enforce pause and human-handover rules before checkout. The kitchen-load figure must include
   all relevant channels, not only this assistant. What counts toward capacity is still provisional.
3. In ONE database transaction, load the active quote and current menu, lock/reserve the slot,
   recheck the rules, save one order, and enqueue a kitchen ticket in an outbox.
   Coordinate menu changes with checkout so the menu cannot change halfway through the transaction.
   A check followed by a separate save is unsafe when two customers confirm together.
4. Use database uniqueness constraints (one placed order per quote, one processing record per
   incoming message). An in-memory no-op is NOT cross-process idempotency.
5. Send the queued ticket from a durable outbox worker, not from the domain object. Retry safely
   using stable ids and the channel's supported deduplication features; do not promise exactly-once
   network delivery. A crash after the database commit must not lose the kitchen ticket.
6. Release reserved capacity if staff reject, in a transaction, with an appropriate notification.
7. Use a durable worker to find overdue orders and deduplicate alerts. A five-minute in-process
   sleep is not enough: deployments, restarts and multiple replicas can interrupt it.

Do not describe atomic capacity booking, durable idempotency, message delivery or owner alerts
as implemented until those adapters and their integration tests exist.

## Run the pretend order

```bash
poetry run python -m restaurant_assistant.interfaces.demo_order
```

This uses explicitly invented menu data, hours and capacity and a fixed test clock. It makes
no network calls and writes nothing to a database.

Expected sequence: summary for two Margherita pizzas plus one tiramisu, total 19,50 EUR,
awaiting customer, awaiting kitchen, accepted.
