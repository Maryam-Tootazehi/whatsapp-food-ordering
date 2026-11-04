# WhatsApp Food Ordering Assistant

A WhatsApp assistant that lets customers of a family restaurant order food for pickup, book a table, and ask questions about the menu, in plain Italian or English.

> **Status:** design and early implementation. A pilot with a real family restaurant has been agreed. The domain layer is being built test-first on example data until the owner interview provides the real menu, hours and capacity.

## The problem

During busy evenings, a small restaurant cannot always answer the phone. Missed calls are lost orders, and orders taken over a noisy phone line are easy to get wrong.

## What the assistant will do (pilot scope)

- **Pickup orders:** the customer writes what they want; the assistant confirms items, total and pickup time, and sends the order to the kitchen only after the customer says yes.
- **Table bookings:** date, time, number of people and name.
- **Menu questions:** ingredients, opening hours and allergens, answered only from data the restaurant has confirmed.
- **Hand-off to staff:** anything the assistant cannot handle goes to a person.

Out of scope for the pilot: delivery, online payment, voice messages.

## Design principles

- **The language model interprets; the code decides.** The LLM only turns a message into structured data. Prices, availability, opening hours and allergens always come from the database, never from the model.
- **Humans stay in control.** Every order needs the customer's explicit confirmation and staff acceptance. The owner can pause the assistant at any time.
- **Privacy by design.** Only the data needed for an order is stored, and pilot data is deleted at the end.

## Planned architecture

| Part | Technology |
|---|---|
| Messaging | WhatsApp Business Platform (Cloud API) |
| Web service | Python, FastAPI |
| Conversation flow | LangGraph |
| Language model | Azure OpenAI |
| Database | Supabase (PostgreSQL) |
| Hosting | Docker on Azure Container Apps |
| CI/CD | GitHub Actions |

The code will follow a hexagonal (layered) architecture based on domain-driven design.

## How the project is developed

The project follows the software engineering process from the *Software Engineering* course of the MSc in Digital Transformation Management (University of Bologna):

1. **Use case collection:** interview with the restaurant owner ([question sheet](docs/requirements/stakeholder-questions.xlsx))
2. **Requirements analysis:** user stories with acceptance criteria
3. **Design:** domain model, glossary, context map and UML diagrams
4. **Implementation** with test-driven development
5. **Verification:** automated tests and acceptance tests with real users
6. **Release and deployment:** semantic versioning, conventional commits, CI/CD
7. **Documentation and maintenance**

## Repository structure

```
src/restaurant_assistant/
  domain/         the restaurant's rules in plain Python: no FastAPI, LangGraph, Supabase or LLM
  application/    use cases and ports (interfaces the outside world must implement)
  storage/        repository adapters: in-memory now, Supabase (PostgreSQL) later
  interfaces/     WhatsApp webhook, language model client, conversation flow (later)
tests/
  unit/           fast, deterministic tests with fakes; no API keys needed
  architecture/   fails the build if a layer imports something it must not
docs/
  requirements/   questions, user stories and requirements
  design/         glossary and architecture (layers and context map)
  adr/            architecture decision records: what we decided and why
```

A test in `tests/architecture/` enforces the hexagonal rule: dependencies point inwards only.

## Development

Requires Python 3.12 and [Poetry](https://python-poetry.org/) 2.

```bash
poetry install
poetry run pytest        # unit and architecture tests, offline
poetry run ruff check .  # lint
poetry run mypy          # strict type checking
```

GitHub Actions runs the same checks on every pull request.

## License

[MIT](LICENSE). Chosen because it is simple and permissive: the goal is to share the work openly as a learning and portfolio project.
