# WhatsApp Food Ordering Assistant

A WhatsApp assistant that lets customers of a family restaurant order food for pickup, book a table, and ask questions about the menu, in plain Italian or English.

> **Status:** requirements phase. A pilot with a real family restaurant has been agreed; no code yet.

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
docs/
  requirements/   questions, user stories and requirements
```

More folders will be added as the project moves into design and implementation.

## License

[MIT](LICENSE). Chosen because it is simple and permissive: the goal is to share the work openly as a learning and portfolio project.
