# Admin API Reference

This document defines the operational admin layer for the multi-provider PesaGuard backend. It covers the core webhook ingress, provider payout routes, and statement-ingestion endpoints used by finance and operations teams.

All admin routes are expected to be protected by the platform admin token and should be tenant-aware when the request is not explicitly scoped.

---

## Authentication

Use the admin token in a request header:

```http
X-Admin-Token: <your-admin-token>
```

Optional tenant scoping:

```http
X-Tenant-ID: tenant-bank
```

If `tenant_id` is present in payload data, that value should be preferred over the header value.

---

## Core webhook routes

### M-Pesa validation callback

- Method: `POST`
- Endpoint: `/webhook/mpesa/validation`
- Purpose: accept or reject a validation callback before transaction completion

Example response:

```json
{
  "ResultCode": 0,
  "ResultDesc": "Accepted"
}
```

### M-Pesa confirmation callback

- Method: `POST`
- Endpoint: `/webhook/mpesa/confirmation`
- Purpose: ingest verified M-Pesa confirmation events into the reconciliation ledger

Success response:

```json
{
  "ResultCode": 0,
  "ResultDesc": "Accepted"
}
```

### Airtel confirmation callback

- Method: `POST`
- Endpoint: `/webhook/airtel/confirmation`
- Purpose: accept Airtel Money confirmation events using the same canonical event contract as the M-Pesa flow

Success response:

```json
{
  "ResultCode": 0,
  "ResultDesc": "Accepted (duplicate ignored)"
}
```

---

## Outbound payout routes

### Airtel Money payout

- Method: `POST`
- Endpoint: `/admin/airtel/payments`
- Purpose: dispatch an Airtel Money outgoing payment using tenant-configured credentials

Request example:

```json
{
  "tenant_id": "tenant-airtel",
  "amount": 2500,
  "currency": "UGX",
  "reference": "INV-AIR-777",
  "msisdn": "256700000001",
  "description": "Loan repayment"
}
```

Success response example:

```json
{
  "status": "accepted",
  "tenant_id": "tenant-airtel",
  "transaction_id": "AIR-123",
  "reference": "INV-AIR-777",
  "amount": 2500,
  "currency": "UGX",
  "payload": {
    "status": "accepted",
    "transactionId": "AIR-123"
  }
}
```

Error example:

```json
{
  "error": "Airtel credentials are not configured for this tenant"
}
```

Contract endpoint:

- `GET /admin/airtel/payments/contracts`

---

### Bank transfer payout

- Method: `POST`
- Endpoint: `/admin/bank/payments`
- Purpose: dispatch a bank transfer request using tenant-configured bank credentials

Request example:

```json
{
  "tenant_id": "tenant-bank",
  "amount": 400,
  "currency": "KES",
  "reference": "INV-BANK-400",
  "account_number": "1234567890",
  "bank_name": "KCB",
  "narration": "Invoice settlement"
}
```

Success response example:

```json
{
  "status": "processed",
  "tenant_id": "tenant-bank",
  "transaction_id": "BANK-123",
  "reference": "INV-BANK-400",
  "amount": 400,
  "currency": "KES",
  "payload": {
    "status": "processed",
    "transactionId": "BANK-123"
  }
}
```

Error example:

```json
{
  "error": "Bank credentials are not configured for this tenant"
}
```

Contract endpoint:

- `GET /admin/bank/payments/contracts`

---

## Bank ingestion routes

### Statement ingestion dispatch

- Method: `POST`
- Endpoint: `/admin/bank/ingest`
- Purpose: ingest bank records from API payloads, CSV content, Excel workbooks, PDF statements, webhook submissions, manual uploads, or SFTP-delivered files

Supported source types:

- `api`
- `csv`
- `excel`
- `pdf`
- `sftp`
- `webhook`
- `manual`

Example payload for CSV import:

```json
{
  "source_type": "csv",
  "tenant_id": "tenant-bank",
  "account_id": "acct-100",
  "file_name": "statement.csv",
  "csv_text": "date,reference,amount,narration,status\n2026-09-01,CSV-100,-120,Fee,POSTED"
}
```

Example payload for Excel import:

```json
{
  "source_type": "excel",
  "tenant_id": "tenant-bank",
  "account_id": "acct-100",
  "bank_name": "KCB",
  "excel_bytes": "base64-encoded-xlsx-content"
}
```

Example payload for webhook import:

```json
{
  "source_type": "webhook",
  "tenant_id": "tenant-bank",
  "payload": {
    "accountId": "acct-100",
    "reference": "WEB-200",
    "amount": "-120",
    "narration": "Webhook bank fee",
    "status": "POSTED",
    "bankName": "KCB"
  }
}
```

Example payload for SFTP import:

```json
{
  "source_type": "sftp",
  "tenant_id": "tenant-bank",
  "host": "sftp.example.com",
  "remote_path": "/incoming/bank_statement.csv",
  "username": "ops-user",
  "password": "secret"
}
```

Contract endpoint:

- `GET /admin/bank/ingest/contracts`

---

## Expected behavior and validation rules

- Amount values must be numeric and greater than zero for all outgoing payment requests.
- Provider credentials must be configured in the tenant settings store before the route dispatches payment requests.
- All callbacks should be treated as idempotent; duplicate transaction references must not be processed more than once.
- Provider contracts are intentionally designed to be consistent with the canonical reconciliation model and should be normalized before ledger storage.

---

## Operational notes

- Keep the admin token scoped to trusted operational users only.
- Prefer tenant-scoped configuration for production deployments with multi-customer isolation.
- Use the contract endpoints as a self-serve reference for integration and QA validation.
- Treat the admin routes as backend operational APIs, not public customer-facing endpoints.
