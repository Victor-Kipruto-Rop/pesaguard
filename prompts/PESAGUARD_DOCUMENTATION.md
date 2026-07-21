# PesaGuard — Technical Documentation

Real-time reconciliation & anomaly detection for M-Pesa-integrated businesses.

**Version:** MVP 0.1
**Last updated:** July 2026

---

## Table of Contents

1. [Overview](#1-overview)
2. [Architecture](#2-architecture)
3. [Project Structure](#3-project-structure)
4. [Getting Started](#4-getting-started)
5. [Environment Variables](#5-environment-variables)
6. [API Reference](#6-api-reference)
7. [Data Models](#7-data-models)
8. [Kafka Topics](#8-kafka-topics)
9. [Anomaly Detection Rules](#9-anomaly-detection-rules)
10. [Internal-System Connectors](#10-internal-system-connectors)
11. [Alerting](#11-alerting)
12. [Testing](#12-testing)
13. [Deployment](#13-deployment)
14. [Troubleshooting](#14-troubleshooting)
15. [Roadmap](#15-roadmap)

---

## 1. Overview

PesaGuard ingests M-Pesa Daraja webhook callbacks, streams them through Kafka,
reconciles them against a business's internal ledger/orders, and alerts on
discrepancies — duplicate transactions, amount mismatches, missing callbacks,
and unusually large payments — in near real-time.

**Core services:**

| Service | Location | Responsibility |
|---|---|---|
| Webhook Receiver | `ingestion/webhook_receiver/` | Validates and ingests Daraja callbacks |
| Reconciliation Job | `streaming/flink_jobs/` | Consumes Kafka stream, applies anomaly rules |
| Dashboard API | `dashboard/api/` | Serves discrepancy/summary data |
| Alerting | `alerting/` | Dispatches Slack notifications on discrepancies |

---

## 2. Architecture

```
                    ┌─────────────────┐
  M-Pesa Daraja ───▶│ Webhook Receiver │
                    │   (Flask)        │
                    └────────┬─────────┘
                             │ validates + publishes
                             ▼
                    ┌─────────────────┐
                    │  Kafka Topic     │
                    │ transactions.raw │
                    └────────┬─────────┘
                             │ consumes
                             ▼
                    ┌─────────────────┐      ┌──────────────────┐
                    │ Reconciliation   │─────▶│ Internal Ledger   │
                    │ Job              │◀─────│ Connector          │
                    └────────┬─────────┘      └──────────────────┘
                             │ writes
                 ┌───────────┴───────────┐
                 ▼                       ▼
        ┌────────────────┐     ┌──────────────────┐
        │  PostgreSQL     │     │  Alerting         │
        │  (transactions,  │     │  (Slack/SMS/email)│
        │   discrepancies) │     └──────────────────┘
        └────────┬────────┘
                 │ reads
                 ▼
        ┌────────────────┐
        │  Dashboard API  │
        │  (Flask)        │
        └────────────────┘
```

**Design principles:**
- Kafka decouples ingestion from processing — the webhook receiver never
  blocks on reconciliation logic, so a slow rule engine can't cause Daraja
  callback timeouts.
- Postgres is the single source of truth for audit purposes; every
  transaction and every discrepancy decision is persisted, not just the
  flagged ones.
- Connectors are pluggable — the reconciliation job doesn't know or care
  whether a tenant's internal data lives in Postgres, Google Sheets, or a
  REST API.

---

## 3. Project Structure

```
pesaguard/
├── ingestion/
│   ├── webhook_receiver/       # Flask app: receives Daraja callbacks
│   │   ├── app.py              # Routes: /webhook/mpesa/confirmation, /validation
│   │   ├── validators.py       # Payload validation
│   │   ├── producer.py         # Kafka publish wrapper
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   └── internal_sync/
│       └── connectors/
│           └── base_connector.py   # Abstract connector interface
│
├── streaming/
│   ├── kafka/
│   │   └── topics.py            # Topic name constants
│   └── flink_jobs/
│       ├── reconciliation_job.py  # Main consumer loop
│       ├── anomaly_rules.py       # Rule definitions
│       ├── requirements.txt
│       └── Dockerfile
│
├── storage/
│   ├── models/
│   │   └── models.py             # SQLAlchemy models
│   └── migrations/
│       └── init_db.py            # Table creation script
│
├── alerting/
│   ├── notifier.py               # Slack webhook dispatch
│   └── templates/
│       └── slack_template.md     # Alert message reference
│
├── dashboard/
│   └── api/
│       ├── app.py                # Discrepancy/summary endpoints
│       ├── requirements.txt
│       └── Dockerfile
│
├── infra/
│   └── docker-compose.yml        # Local dev stack
│
├── tests/
│   └── test_anomaly_rules.py
│
├── .env.example
└── README.md
```

---

## 4. Getting Started

### Prerequisites

- Docker & Docker Compose
- Python 3.11+ (for running scripts outside containers)
- A Daraja sandbox account ([Safaricom Developer Portal](https://developer.safaricom.co.ke/))

### Setup

```bash
# 1. Clone/extract the project, then:
cp .env.example .env

# 2. Fill in .env with:
#    - Daraja sandbox credentials
#    - SLACK_WEBHOOK_URL (optional for local dev — logs instead if unset)

# 3. Start the stack
cd infra/
docker-compose up -d

# 4. Initialize the database
python storage/migrations/init_db.py

# 5. Verify services are healthy
curl http://localhost:5000/health   # webhook receiver
curl http://localhost:5001/api/stats/summary   # dashboard API
```

### Exposing your local webhook receiver to Daraja

Daraja needs a public URL to send callbacks to. For local development, use
a tunnel:

```bash
ngrok http 5000
# Register the ngrok URL + /webhook/mpesa/confirmation as your
# ConfirmationURL in the Daraja sandbox portal
```

### Running services individually (without Docker)

```bash
# Webhook receiver
cd ingestion/webhook_receiver
pip install -r requirements.txt --break-system-packages
python app.py

# Reconciliation job
cd streaming/flink_jobs
pip install -r requirements.txt --break-system-packages
python reconciliation_job.py

# Dashboard API
cd dashboard/api
pip install -r requirements.txt --break-system-packages
python app.py
```

---

## 5. Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `DARAJA_CONSUMER_KEY` | Yes (prod) | — | Daraja API consumer key |
| `DARAJA_CONSUMER_SECRET` | Yes (prod) | — | Daraja API consumer secret |
| `DARAJA_SHORTCODE` | Yes (prod) | — | Business shortcode/till number |
| `DARAJA_ENV` | No | `sandbox` | `sandbox` or `production` |
| `KAFKA_BOOTSTRAP_SERVERS` | No | `localhost:9092` | Kafka broker address |
| `KAFKA_TOPIC_TRANSACTIONS` | No | `mpesa.transactions.raw` | Raw ingestion topic |
| `KAFKA_TOPIC_MATCHED` | No | `mpesa.transactions.matched` | Clean reconciliations |
| `KAFKA_TOPIC_DISCREPANCIES` | No | `mpesa.discrepancies` | Flagged anomalies |
| `DATABASE_URL` | No | `postgresql://pesaguard:pesaguard@localhost:5432/pesaguard` | Postgres connection string |
| `SLACK_WEBHOOK_URL` | No | — | If unset, alerts are logged instead of sent |
| `PORT` | No | `5000` | Webhook receiver port |
| `DASHBOARD_API_PORT` | No | `5001` | Dashboard API port |

---

## 6. API Reference

### Webhook Receiver (`ingestion/webhook_receiver`)

#### `POST /webhook/mpesa/confirmation`

Receives C2B confirmation callbacks from Daraja after a payment completes.

**Request body** (Daraja-defined shape):
```json
{
  "TransactionType": "Pay Bill",
  "TransID": "OEI2AK4Q16",
  "TransTime": "20260702143000",
  "TransAmount": "500.00",
  "BusinessShortCode": "600000",
  "MSISDN": "254712345678"
}
```

**Response:**
```json
{ "ResultCode": 0, "ResultDesc": "Accepted" }
```
Returns `ResultCode: 1` with a 400 status if the payload fails validation
(missing required fields, non-numeric amount, empty `TransID`).

#### `POST /webhook/mpesa/validation`

Receives C2B validation callbacks (pre-confirmation). Currently accepts all
transactions by default — add business rules in `app.py` if you need to
reject certain transactions before completion (e.g. invalid account format).

#### `GET /health`

Returns `{"status": "ok"}` — used for container/orchestration health checks.

---

### Dashboard API (`dashboard/api`)

#### `GET /api/discrepancies`

Returns all unresolved discrepancies, most recent first.

**Response:**
```json
[
  {
    "id": "OEI2AK4Q16-duplicate_transaction_id",
    "trans_id": "OEI2AK4Q16",
    "anomaly_type": "duplicate_transaction_id",
    "details": null,
    "detected_at": "2026-07-02T14:30:12+00:00"
  }
]
```

#### `GET /api/stats/summary`

Returns a high-level reconciliation snapshot.

**Response:**
```json
{
  "total_transactions": 4213,
  "open_discrepancies": 7,
  "reconciliation_rate": 0.9983
}
```

---

## 7. Data Models

Defined in `storage/models/models.py` (SQLAlchemy).

### `Transaction`
| Column | Type | Notes |
|---|---|---|
| `trans_id` | String (PK) | M-Pesa transaction ID |
| `trans_amount` | Float | |
| `msisdn` | String | Payer phone number |
| `business_short_code` | String | |
| `trans_time` | String | Raw Daraja timestamp format |
| `raw_payload` | JSON | Full original callback payload |
| `created_at` | DateTime | |

### `Discrepancy`
| Column | Type | Notes |
|---|---|---|
| `id` | String (PK) | `{trans_id}-{rule_name}` |
| `trans_id` | String | |
| `anomaly_type` | String | e.g. `duplicate_transaction_id` |
| `details` | Text | Free-form notes |
| `resolved` | Boolean | Default `false` |
| `detected_at` | DateTime | |
| `resolved_at` | DateTime | Nullable |

### `InternalRecord`
| Column | Type | Notes |
|---|---|---|
| `internal_ref` | String (PK) | Order/invoice ID in customer's system |
| `amount` | Float | |
| `phone_number` | String | |
| `status` | String | e.g. `pending`, `paid`, `failed` |
| `synced_at` | DateTime | |

---

## 8. Kafka Topics

Defined in `streaming/kafka/topics.py`.

| Topic | Producer | Consumer | Purpose |
|---|---|---|---|
| `mpesa.transactions.raw` | Webhook Receiver | Reconciliation Job | Every validated incoming M-Pesa event |
| `mpesa.transactions.matched` | Reconciliation Job | (future: analytics) | Transactions that passed all checks cleanly |
| `mpesa.discrepancies` | Reconciliation Job | Alerting | Transactions that failed one or more anomaly rules |

---

## 9. Anomaly Detection Rules

Defined in `streaming/flink_jobs/anomaly_rules.py`. Each rule is independent
and returns a string identifier if triggered; a transaction can trigger
multiple rules at once.

| Rule | Trigger Condition | Configurable? |
|---|---|---|
| `duplicate_transaction_id` | `TransID` already seen in this run | No (in-memory set; use Redis/DB for production) |
| `amount_exceeds_threshold_{N}_KES` | `TransAmount` > `LARGE_AMOUNT_THRESHOLD_KES` (default 150,000) | Yes — edit constant in `anomaly_rules.py` |
| `invalid_or_zero_amount` | `TransAmount` is ≤ 0 or non-numeric | No |

**Not yet implemented** (see [Roadmap](#15-roadmap)):
- `missing_internal_record` — M-Pesa confirms payment, no matching internal order
- `amount_mismatch` — M-Pesa amount ≠ internal record amount
- `till_number_mismatch`

---

## 10. Internal-System Connectors

Defined in `ingestion/internal_sync/connectors/base_connector.py`.

All connectors implement:
```python
def fetch_recent_records(self, since_minutes: int = 15) -> Iterable[Dict]:
    """Returns normalized records:
    { "internal_ref": str, "amount": float, "phone_number": str,
      "timestamp": str (ISO8601), "status": str }
    """
```

**Provided stubs** (require implementation before use):
- `PostgresConnector` — queries a customer's orders table directly
- `GoogleSheetsConnector` — reads from a customer's tracking sheet

To add a new connector, subclass `BaseConnector` and implement
`fetch_recent_records()`, returning records in the normalized shape above.

---

## 11. Alerting

`alerting/notifier.py::send_slack_alert()` posts to `SLACK_WEBHOOK_URL`. If
unset, it logs the discrepancy instead of failing — safe for local dev
without a real Slack workspace.

**Message format** (see `alerting/templates/slack_template.md`):
```
🚨 PesaGuard Discrepancy Detected
Transaction: {trans_id}
Issues: {anomaly_list}
Detected at: {timestamp}
```

To add SMS or email channels, add a new function alongside
`send_slack_alert()` in `notifier.py` and call it from the reconciliation
job wherever discrepancies are dispatched.

---

## 12. Testing

```bash
pip install pytest --break-system-packages
pytest tests/
```

Current coverage: anomaly rule logic (`test_anomaly_rules.py`) — clean
transactions, duplicates, large amounts, zero/invalid amounts.

**Not yet covered** (see Roadmap): webhook payload validation edge cases,
Kafka producer/consumer integration, connector implementations, dashboard
API endpoints.

---

## 13. Deployment

### Local / Development
`docker-compose up -d` from `infra/` — starts Zookeeper, Kafka, Postgres,
and all three application services.

### Production (recommended path for early pilots)
Single VM running the same `docker-compose.yml`. Sufficient for one to a
handful of pilot tenants. Migrate to Kubernetes only once tenant count or
throughput genuinely requires it — avoid the added operational overhead
until it's justified.

**Before going to production:**
- Set `DARAJA_ENV=production` and use live Daraja credentials
- Set a real `SLACK_WEBHOOK_URL`
- Move `DATABASE_URL` to a managed Postgres instance (backups matter for
  financial data)
- Put the webhook receiver behind HTTPS (Daraja requires a public HTTPS
  `ConfirmationURL`)
- Review the [Kenya Data Protection Act](https://www.odpc.go.ke/) obligations
  for storing customer transaction data

---

## 14. Troubleshooting

| Symptom | Likely Cause | Fix |
|---|---|---|
| Webhook receiver returns 400 | Payload missing required Daraja fields | Check `validators.py::REQUIRED_FIELDS`; confirm Daraja is sending the expected callback type |
| No events reaching Kafka | Kafka not reachable from webhook receiver | Check `KAFKA_BOOTSTRAP_SERVERS`; confirm Kafka container is healthy (`docker-compose ps`) |
| Reconciliation job not consuming | Consumer group offset issue or Kafka down | Check `docker-compose logs kafka`; verify topic exists |
| No Slack alerts arriving | `SLACK_WEBHOOK_URL` unset or invalid | Check logs — alerts are logged locally if the webhook URL is missing |
| Dashboard API returns empty stats | `init_db.py` not run, or `DATABASE_URL` mismatch between services | Re-run migrations; confirm all services share the same `.env` |
| Duplicate alerts for the same transaction | In-memory dedupe set reset (e.g. service restart) | Expected at MVP scale — see Roadmap for persistent dedupe |

---

## 15. Roadmap

Items intentionally deferred from the MVP, in rough priority order:

1. **Real cross-system matching** — phone+amount+time-window matching against
   internal records (currently only intra-M-Pesa-stream anomalies are detected)
2. **Persistent deduplication** — replace in-memory `seen_trans_ids` with
   Redis or a DB unique constraint so restarts don't lose dedupe state
3. **Multi-tenancy** — scope all tables/topics/API routes by `tenant_id`
4. **Connector implementations** — finish `PostgresConnector` and
   `GoogleSheetsConnector` against a real pilot customer's system
5. **Dashboard frontend** — Next.js UI consuming the existing API
6. **SMS alerting** via Africa's Talking
7. **Dead-letter queue** for events that fail processing, so nothing is
   silently dropped
8. **Structured JSON logging** with `tenant_id`/`trans_id` correlation

For the full phased build plan and detailed requirements, see
`PesaGuard_Project_Blueprint.pdf`. For a ready-to-use prompt to accelerate
this roadmap with an AI coding agent, see `PESAGUARD_BUILD_PROMPT.md`.
