# ADR 0001: Hexagonal architecture with four layers

**Status:** accepted · **Date:** 2026-11-04

## Context
The assistant depends on services that will change during the pilot: the WhatsApp test number
becomes the real number, Azure OpenAI may be swapped for another provider, Supabase is the
database. The restaurant's rules (prices, hours, capacity, allergens) must not change when they do.

## Decision
Four layers: `domain`, `application`, `storage`, `interfaces`. The domain has no framework or I/O
imports; the application defines ports (Protocols); storage and interfaces implement them.
An architecture test enforces the import rules in CI.

## Consequences
+ Domain tests run in milliseconds without keys or network, with the same result every time.
+ Swapping WhatsApp test number → real number, or the LLM provider, touches one adapter.
− More files and some mapping code between database rows and domain objects.
