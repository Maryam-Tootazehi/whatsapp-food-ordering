# ADR 0002: The language model interprets; the code decides

**Status:** accepted · **Date:** 2026-11-04

## Context
LLMs can invent prices, opening hours or allergen facts. For a real restaurant that is a
financial and health risk.

## Decision
The LLM is called in exactly one step: turn a customer message into structured intent
(items as written, quantities, time, language, intent type). It never sees prices, never produces
customer-facing facts, and its output is validated against a schema. Matching text to dishes,
pricing, slot checks and allergen answers are deterministic domain code over owner-confirmed data.
Allergen answers say "contains" / "not declared" / "unknown"; unknown or serious cases go to staff.

## Consequences
+ Every fact a customer sees can be traced to a database row the owner confirmed.
+ The model can be evaluated separately (≈50 realistic messages) and swapped by configuration.
− Replies are template-based and less "chatty"; that is acceptable for ordering.
