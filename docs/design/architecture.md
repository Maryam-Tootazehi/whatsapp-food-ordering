# Architecture

## The one rule
**The language model only interprets; the code decides.** The LLM turns
"due margherite per le 20" into `{"items": [{"text": "margherite", "qty": 2}], "time": "20:00"}`.
Everything after that (which dish, price, total, whether 20:00 is open and the kitchen has room,
what allergens a dish has) is deterministic code reading owner-confirmed data. See ADR 0002.

## Layers (hexagonal / ports and adapters)

```
interfaces  ->  application  ->  domain
storage     ->  application  ->  domain
```

- **domain**: entities, value objects, aggregates and domain services. Pure Python, no I/O,
  no clock (time is passed in as `now`), no frameworks. Fast, deterministic tests.
- **application**: use cases ("quote a pickup order", "confirm an order") and **ports**:
  Protocols such as `MenuRepository`, `Clock`, `IntentExtractor`, `MessagingChannel`.
- **storage**: adapters implementing repository ports (in-memory for tests, Postgres/Supabase).
- **interfaces**: adapters for the outside world: FastAPI webhook, WhatsApp Cloud API (or the
  test number), the Azure OpenAI client behind one `extract_intent()` function, LangGraph flow.

Dependencies point inwards only. `tests/architecture/test_layers.py` fails the build if the
domain imports FastAPI, LangGraph, Supabase, an LLM SDK, or an outer layer.

## Bounded contexts

| Context | Owns | Talks to |
|---|---|---|
| Menu | MenuItem, Category, Allergen, AllergenDeclaration, MenuMatcher | read by Ordering, Conversation |
| Ordering | PickupOrder (aggregate), OrderLine, Quote, PickupPolicy | Menu (prices), Kitchen (capacity) |
| Kitchen | KitchenCapacity, Ticket, acceptance timeout | receives confirmed orders |
| Booking | Booking (aggregate), table capacity | OpeningHours |
| Conversation | where each chat stands, handover, pause | calls Ordering/Booking use cases |

`Money`, `Slot` and `OpeningHours` form a small **shared kernel**: value objects every context
uses, kept tiny on purpose.
