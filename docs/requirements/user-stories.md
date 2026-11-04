# User stories

Format: *As a ..., I want ..., so that ...*, then Given/When/Then acceptance criteria.
Each criterion becomes at least one automated test; the test name says which story it covers.
IDs are stable; stories marked **(draft)** wait for the owner meeting.

## Epic M: Menu

### M1. Recognise the dish the customer means
As a customer, I want to write dishes the way I normally would, so that I don't need the exact menu name.

- **Given** the menu has "Margherita", **when** I write "margherita", "Margherita!" or "MARGHERITA", **then** it matches Margherita.
- **Given** the menu has "Tiramisù", **when** I write "tiramisu", **then** it matches Tiramisù (accents ignored).
- **Given** the menu has "Margherita", **when** I write "margherite" (Italian plural), **then** it matches Margherita.
- **Given** the owner added the alias "marghe", **when** I write "marghe", **then** it matches Margherita.
- **Given** the menu has "Capricciosa", **when** I write "capriciosa" (typo), **then** it matches Capricciosa.
- **Given** the menu has "Calzone fritto" and "Calzone al forno", **when** I write "calzone", **then** the result is ambiguous with both, so the assistant can ask which one.
- **Given** nothing on the menu resembles "sushi", **when** I write "sushi", **then** there is no match and nothing is guessed.
- **Given** "Diavola" is sold out today, **when** I write "diavola", **then** it still matches Diavola, so the assistant can say it is sold out instead of "we don't have it".

### M2. Prices come only from the menu
As the owner, I want every price to come from my menu, so that customers are never quoted a wrong price.

- **Given** a price of €8,50, **then** it is stored as 850 cents, never as a float.
- **Given** 2 × Margherita at €7,00 and 1 × Tiramisù at €5,50, **when** the total is computed, **then** it is €19,50.
- **Given** an amount, **when** shown to an Italian customer, **then** it reads "19,50 €"; to an English customer, "€19.50".

### M3. Allergen answers only from confirmed data
As a customer with an allergy, I want correct allergen information or a real person, so that I am never put at risk by a guess.

- **Given** the owner confirmed Margherita contains gluten and milk, **when** asked about milk, **then** the answer is "contains".
- **Given** the owner confirmed Margherita's allergens and fish is not among them, **when** asked about fish, **then** the answer is "not declared" (never "safe" or "free from").
- **Given** the owner has not confirmed a dish's allergens, **when** asked, **then** the answer is "unknown" and the conversation goes to staff.
- **Given** an allergen cell in the owner's menu sheet is empty or "Non so", **when** the menu is imported, **then** that dish's allergens stay unconfirmed; an empty cell never becomes "No".

## Epic O: Pickup orders

### O1. Check the pickup time
As the owner, I want pickups only at times we are open and the kitchen has room, so that we never promise what we can't deliver.

- **Given** dinner service 19:00–22:30, **when** a customer asks for 20:00 at 18:00 the same day, **then** the slot 20:00–20:15 is accepted.
- **Given** dinner service 19:00–22:30, **when** a customer asks for 23:00, **then** it is refused as closed.
- **Given** the restaurant is closed on Mondays, **when** a customer asks for Monday 20:00, **then** it is refused as closed.
- **Given** a 20-minute lead time, **when** at 19:50 a customer asks for 20:00, **then** it is refused as too soon.
- **Given** a time in the past, **then** it is refused as in the past.
- **Given** capacity 10 items per slot and 8 already booked in 20:00–20:15, **when** a customer orders 3 items for 20:00, **then** it is refused as kitchen full.
- **Given** a refused time, **then** the next possible slots are suggested.
- **Given** a time like 20:07, **then** it falls into the 20:00–20:15 slot.

### O2. Confirm before ordering (next PR)
- **Given** a valid quote, **when** the assistant sends the summary, **then** nothing is saved until the customer confirms.
- **Given** a quote, **when** the customer replies "sì" / "si" / "yes" / taps the Confirm button, **then** the order is saved and sent to the kitchen.
- **Given** a quote, **when** the customer confirms, **then** availability, price and kitchen capacity are checked again in the same database transaction that saves the order, so two customers confirming at once cannot overbook one slot.
- **Given** a quote older than 10 minutes, **when** the customer confirms, **then** the customer gets a fresh summary to confirm instead.

### O3. Kitchen acceptance alert (draft)
- **Given** a placed order, **when** staff have not accepted it within 5 minutes, **then** the owner gets an alert.

## Epic C: Conversation (draft)
- C1. Customer can ask for a person at any time; the assistant stops replying in that chat.
- C2. The owner can pause the assistant; customers get a short message with the phone number.
- C3. Italian or English: the assistant answers in the customer's language.

## Epic B: Bookings (draft, after the owner meeting)
- B1. Book a table for N people at a time, checked against opening hours and table capacity.
