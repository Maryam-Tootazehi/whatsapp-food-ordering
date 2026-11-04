# ADR 0003: Money as integer cents

**Status:** accepted · **Date:** 2026-11-04

## Decision
`Money` is an immutable value object holding an `int` number of euro cents. Floats are rejected
(0.1 + 0.2 != 0.3 in binary floating point). Parsing from text uses `Decimal`. Prices include VAT,
as Italian menus do. Totals are sums of `unit price × quantity`; no division, so no rounding yet.
In Postgres the column will be `integer` (cents), not `numeric` or `float`.
