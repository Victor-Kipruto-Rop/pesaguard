# Airtel Money Integration Contract

This document defines the tenant configuration, webhook contract, and outbound payment request pattern for Airtel Money in PesaGuard.

## 1. Tenant configuration

Add these values to the tenant environment or a tenant-scoped override:

```bash
AIRTEL_BASE_URL=https://sandbox.example.com
AIRTEL_API_KEY=your_airtel_api_key_here
AIRTEL_API_SECRET=your_airtel_api_secret_here
```

For per-tenant overrides, use:

```bash
ACME_AIRTEL_BASE_URL=https://sandbox.example.com
ACME_AIRTEL_API_KEY=your_airtel_api_key_here
ACME_AIRTEL_API_SECRET=your_airtel_api_secret_here
```

The loader in `pesaguard_backend_pipeline/shared/airtel/config.py` resolves:

1. tenant-scoped values first
2. global Airtel env values second
3. safe default sandbox values if unset

## 2. Webhook callback contract

PesaGuard accepts Airtel callback payloads on:

```http
POST /webhook/airtel/confirmation
```

Minimum accepted payload structure:

```json
{
  "transactionId": "AIR-100001",
  "amount": 2500,
  "currency": "UGX",
  "status": "success",
  "msisdn": "256700000001",
  "transactionType": "AIRTEL_MONEY",
  "transactionTime": "2026-09-06T11:22:33Z"
}
```

Accepted alternative keys:

- `TransactionId`
- `id`
- `phoneNumber`
- `senderMsisdn`
- `MSISDN`
- `transactionStatus`
- `timestamp`

The validator enforces:

- valid transaction ID
- positive numeric amount
- required status field
- valid phone number format when provided
- currency/amount relationship for outbound payment-aware flows

## 3. Outbound payment request helper

Use the Airtel payment client for disbursements or crediting a wallet:

```python
from pesaguard_backend_pipeline.shared.airtel.payment_client import AirtelPaymentClient

client = AirtelPaymentClient(
    tenant_id="acme",
    credentials={
        "api_key": "...",
        "api_secret": "...",
        "base_url": "https://sandbox.example.com",
    },
)

response = client.request_payment(
    amount=2500,
    currency="UGX",
    reference="INV-777",
    msisdn="256700000001",
    description="Loan repayment",
)
```

Standard request payload build:

```python
payload = client.build_disbursement_payload(
    amount=2500,
    currency="UGX",
    reference="INV-777",
    msisdn="256700000001",
    description="Loan repayment",
)
```

This emits a normalized payload shaped like:

```json
{
  "amount": 2500,
  "currency": "UGX",
  "reference": "INV-777",
  "msisdn": "256700000001",
  "description": "Loan repayment"
}
```

## 4. Reconciliation behavior

The provider resolver in `pesaguard_backend_pipeline/reconciliation_engine.py` classifies events as:

- `airtel` for Airtel transaction IDs / Airtel transaction metadata
- `daraja` for M-Pesa Daraja payloads
- `unknown` otherwise

This is used in reconciliation results so downstream audits and dashboards can distinguish provider-specific events.

## 5. Security notes

- Treat Airtel credentials as sensitive and rotate them on the provider schedule.
- Prefer tenant-scoped variables for multi-tenant deployments.
- Always validate callback signatures or source origin when Airtel requires them.
- Keep the webhook endpoint idempotent using the transaction ID as the dedupe key.
