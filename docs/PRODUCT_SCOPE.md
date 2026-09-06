# PesaGuard Product Scope Decision

This document satisfies requirements **SCOPE-1** through **SCOPE-4** from Addendum III.

---

## Current scope (SCOPE-1)

**PesaGuard reconciles M-Pesa, Airtel Money, and bank-transfer transactions using provider-aware reconciliation logic and tenant-scoped configuration.**

| In scope | Out of scope (future phase) |
|---|---|
| M-Pesa C2B/B2C webhook ingestion | Card payments, PayPal, other non-bank rails |
| Daraja transaction status queries | Additional country-specific rails beyond the approved providers |
| Airtel Money callback validation and payout helpers | Broad product expansion without a customer requirement |
| Bank transfer payout requests and normalized transfer reconciliation | Advanced treasury features outside the core settlement/reconciliation model |
| Internal-ledger matching (Postgres, Sheets, REST) against normalized payment records | Multi-rail unified payment inbox beyond the supported providers |
| Anomaly detection on provider reconciliation gaps | Broad product expansion without a customer requirement |

**Timeline for expansion:** The core product now supports three major rails, and further expansion remains gated by concrete pilot requirements and scoping review rather than ad hoc feature creep (**SCOPE-4**).

---

## Reasoning

1. The entire ingestion pipeline, webhook validators, and Daraja auth client are M-Pesa-specific today.
2. Pilot positioning targets SACCOs and SMEs whose primary payment pain is M-Pesa reconciliation.
3. Building Airtel Money or bank connectors speculatively would delay pilot value without validated demand.

---

## Customer-facing statement (SCOPE-2)

> PesaGuard monitors and reconciles **M-Pesa (Daraja), Airtel Money, and bank transfer transactions** through provider-aware reconciliation workflows. If your business accepts additional payment methods such as card payments, wallets, or other rails beyond the approved list, those transactions are not included in reconciliation or alerting until a future release. Contact us if multi-rail support is a hard requirement — that becomes a separate scoping conversation.

This statement appears in:

- Dashboard scope banner (`scope.label` in locale files)
- `docs/customer/GETTING_STARTED_en.md` and `GETTING_STARTED_sw.md`
- `docs/customer/FAQ_en.md` and `FAQ_sw.md`

---

## Future expansion path (SCOPE-3)

If a pilot customer requires multi-payment-method reconciliation, evaluate reusing the existing **`BaseConnector`** pattern as a **`PaymentSourceConnector`** abstraction:

```python
# Conceptual — not implemented until a customer requirement justifies it
class PaymentSourceConnector(ABC):
    @abstractmethod
    def fetch_recent_payments(self, since_minutes: int) -> Iterable[Dict[str, Any]]:
        """Normalized: payment_ref, amount, payer_id, timestamp, rail, status"""
        ...
```

| Existing pattern | Reuse for payment rails |
|---|---|
| `BaseConnector.fetch_recent_records()` | Same normalized-record idea for internal ledger |
| `ConnectorRegistry.from_env()` | Per-tenant, per-rail connector registration |
| Reconciliation job matching logic | Should compare on normalized fields, not M-Pesa-specific keys |

**Do not refactor core reconciliation to this pattern until a paying customer needs a second rail.** Document the evaluation here; implement when scoped.

### Rails under consideration (unordered, uncommitted)

| Rail | Integration path | Effort estimate | Status |
|---|---|---|---|
| Airtel Money | Partner API / file export | Medium–High | In scope |
| Bank transfers | Open banking / settlement API | High | In scope |
| Additional M-Pesa products | Daraja APIs already partially integrated | Low–Medium | In scope via Daraja |

---

## When a pilot asks for multi-rail support (SCOPE-4)

1. **Do not** silently add connectors during the current build.
2. Schedule a scoping call using Phase 0 discovery questions:
   - *"Besides M-Pesa, do you take payments through Airtel Money, bank transfer, or any other rail we'd need to reconcile?"*
3. Produce a separate phase proposal: connectors needed, timeline, pricing, residency impact.
4. Update this document with the agreed expansion plan before development starts.

---

## Validation

Kiswahili scope statements and customer docs should be reviewed by a Kiswahili-speaking user or pilot candidate before being treated as final (*pending real-world input*).

---

## Related files

- `pesaguard_backend_pipeline/base_connector.py` — internal ledger connector pattern
- `frontend/locales/en.json` / `sw.json` — dashboard scope banner
- `docs/customer/GETTING_STARTED_*.md`, `FAQ_*.md` — onboarding copy
