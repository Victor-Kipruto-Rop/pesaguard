# Product Scope Decision

## Current scope

PesaGuard is currently scoped to M-Pesa reconciliation and monitoring through the Daraja integration path. This scope is the default baseline for pilot deployments and documentation.

## Out of scope for now

- Airtel Money reconciliation
- Bank transfer reconciliation
- Other non-M-Pesa payment methods

## Reasoning

The current implementation and pilot positioning are centered on M-Pesa workflows. Expanding beyond M-Pesa should only occur when a real customer requirement makes the broader scope concrete and commercially justified.

## Expansion path

If broader payment-method support becomes necessary, the next step should be a separate scoping exercise that evaluates connector reuse, tenant needs, and the operational impact of adding new payment sources.

## Customer-facing statement

Customers should be told clearly that the platform currently reconciles M-Pesa/Daraja-based transactions and does not yet cover other payment methods.
