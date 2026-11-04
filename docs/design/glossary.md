# Glossary (ubiquitous language)

The words we use in code, tests, docs and conversations with the owner. When the owner uses a
different word at the meeting, **we change the glossary and the code**, not the other way round.
Status: draft, to be validated at the owner meeting.

| Term (code) | Italiano | Meaning |
|---|---|---|
| `Owner` | Titolare | Runs the restaurant; confirms menu, prices, allergens; can pause the assistant. |
| `Staff` | Personale | People in the restaurant who accept orders and answer handovers. |
| `Customer` | Cliente | Someone writing on WhatsApp, identified by phone number. |
| `MenuItem` | Piatto / voce di menu | Something a customer can order, with a price. |
| `Category` | Categoria | Antipasti, Pizze, Dolci, Bevande... |
| `Alias` | Nome alternativo | Another name customers use for a dish ("marghe" → Margherita). Owner-approved. |
| `Available` / sold out | Disponibile / esaurito | Whether a dish can be ordered today. |
| `Money` | Prezzo / importo | An amount in **euro cents** (850 = €8,50). VAT (IVA) is included, as on Italian menus. |
| `Allergen` | Allergene | One of the 14 allergens of EU Regulation 1169/2011. |
| `AllergenDeclaration` | Dichiarazione allergeni | The allergens of a dish **as confirmed by the owner**, with who and when. Missing confirmation means "unknown", never "no". |
| `PickupOrder` | Ordine da asporto | An order the customer collects at the restaurant. |
| `OrderLine` | Riga d'ordine | One dish and a quantity in an order. |
| `Quote` | Riepilogo | The summary (items, total, pickup time) the customer must confirm with "sì". |
| `Confirmation` | Conferma | The customer's explicit "sì" to a quote. Only then is an order placed. |
| `Ticket` | Comanda | The order as the kitchen receives it. |
| `Slot` | Fascia oraria | A time interval, e.g. 20:00–20:15, used for pickups and bookings. |
| `Service` | Servizio (pranzo / cena) | An opening window: lunch or dinner. |
| `OpeningHours` | Orari di apertura | Services per weekday. |
| `KitchenCapacity` | Capacità della cucina | How many items the kitchen can prepare per slot. |
| `LeadTime` | Tempo minimo di preparazione | Minimum time between ordering and pickup. |
| `Booking` | Prenotazione | A reserved table for a party at a slot. |
| `Covers` | Coperti | Number of people in a booking. |
| `Handover` | Passaggio a una persona | The conversation is handed to staff; the assistant stops replying. |
| `Pause` | Pausa | Owner switch: the assistant stops taking orders and bookings. |
