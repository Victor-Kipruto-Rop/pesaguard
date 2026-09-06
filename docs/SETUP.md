# PesaGuard Setup & Deployment Guide

This setup guide defines the operational baseline for running the PesaGuard backend in a local environment and preparing it for a premium pilot or production deployment. It is intentionally aligned with the product positioning in [README.md](../README.md) and the operational route contracts in [ADMIN_API.md](ADMIN_API.md).

---

## 1. Prerequisites

PesaGuard is designed for a modern Python backend with PostgreSQL, Redis, and Kafka-friendly operational patterns. A typical local setup includes:

- Python 3.11+
- PostgreSQL for primary persistence
- Redis for caching and idempotency-related support
- Kafka for asynchronous event publication and downstream processing
- Docker Compose for dependency orchestration
- A tenant-aware configuration model for provider credentials

---

## 2. Local environment setup

Create the virtual environment and install the project dependencies:

```bash
cd /path/to/pesaguard
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt pytest pyyaml sqlalchemy psycopg2-binary requests
```

If a sample environment file exists, copy it and populate the real runtime values:

```bash
cp .env.example .env 2>/dev/null || true
```

---

## 3. Required environment values

Provide the minimum runtime settings required to run the platform securely and predictably:

```env
DATABASE_URL=postgresql://pesaguard:pesaguard@localhost:5432/pesaguard
TENANT_ID=default
REDIS_URL=redis://localhost:6379/0
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
PESAGUARD_ADMIN_API_TOKEN=your-admin-token

CONNECTOR_TYPE=postgres
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...

DARAJA_BASE_URL=https://sandbox.safaricom.co.ke
DARAJA_CONSUMER_KEY=your_daraja_consumer_key_here
DARAJA_CONSUMER_SECRET=your_daraja_consumer_secret_here

AIRTEL_BASE_URL=https://sandbox.example.com
AIRTEL_API_KEY=your_airtel_api_key_here
AIRTEL_API_SECRET=your_airtel_api_secret_here

BANK_BASE_URL=https://api.bank.example
BANK_API_KEY=your_bank_api_key_here
BANK_API_SECRET=your_bank_api_secret_here
BANK_PARTNER_CODE=your_bank_partner_code_here
```

### Minimum required settings

- `DATABASE_URL` for PostgreSQL persistence
- `TENANT_ID` for tenant-scoped routing and configuration
- `DARAJA_*` credentials for M-Pesa integration
- `AIRTEL_*` credentials for Airtel Money payout and callback processing
- `BANK_*` credentials for bank transfer request flows
- `PESAGUARD_ADMIN_API_TOKEN` for protected admin endpoints

Optional but useful:

- `REDIS_URL`
- `KAFKA_BOOTSTRAP_SERVERS`
- `SLACK_WEBHOOK_URL`
- custom regional or environment-specific provider overrides

---

## 4. Running the stack locally

Start the dependent services:

```bash
docker-compose up -d postgres kafka redis
```

Initialize the database:

```bash
python init_db.py
```

Then start the backend services:

```bash
python -m pesaguard_backend_pipeline.app
python -m pesaguard_backend_pipeline.reconciliation_job
python -m pesaguard_backend_pipeline.alerting_consumer
```

If the project is running in the Dockerized or deployment environment, use the repository-provided compose definitions and service startup scripts instead of the raw local commands.

---

## 5. Running the test suite

Use the repository test suite to validate the backend behavior and new provider flows:

```bash
pytest -q
```

For a more focused validation, you can run the provider-specific tests as needed:

```bash
PYTHONPATH=. .venv/bin/python -m pytest pesaguard_backend_pipeline/tests/test_airtel_provider_flow.py -q
```

---

## 6. Tenant onboarding checklist

For each new tenant or pilot customer:

- configure a tenant-specific provider map and credentials
- validate callback and payout metadata for M-Pesa, Airtel Money, and/or bank rails
- confirm the connector exposes normalized fields such as `internal_ref`, `amount`, `phone_number`, `timestamp`, and `status`
- run the reconciliation flow in shadow mode for at least one business cycle
- review discrepancy output before enabling live alerts or payout automation

This ensures onboarding remains operationally safe instead of feature-driven by assumption.

---

## 7. Operational notes

- The reconciliation engine treats duplicate callbacks and missing-payment scenarios as critical exceptions and records them in the discrepancy stream.
- The alerting consumer, `pesaguard_backend_pipeline.alerting_consumer`, handles downstream notification logic without coupling alert routing directly into the reconciliation job.
- The connector layer is tenant-scoped so new customers can be onboarded by configuration changes rather than new business logic.
- If the provider callback schema changes, validate the payload against the sandbox configuration and update the payload validator before production release.
- All admin routes should be treated as operational backend endpoints and protected with strong credentials and tenant-level access control.

---

## 8. Monitoring, metrics, and operator readiness

PesaGuard is designed to be operator-friendly in real finance environments:

- alerts are routed through the alerting service with severity-aware channels and deduplication support
- each backend service exposes a Prometheus-compatible `/metrics` endpoint
- a Grafana dashboard definition is available at [monitoring/grafana-dashboard.json](../monitoring/grafana-dashboard.json)
- local verification should include scraping the metrics endpoints:

```bash
http://127.0.0.1:5000/metrics
http://127.0.0.1:5001/metrics
```

A basic operator runbook should cover:

- Kafka lag and downstream processing delays
- connector auth failures and provider outages
- reconciliation spikes or unexplained discrepancy volume
- duplicate callback anomalies and retry storms

---

## 9. Production hardening checklist

Before going live with a pilot or production deployment, verify:

- tenant credentials are isolated and encrypted where required
- provider secrets are rotated as part of the operational process
- admin routes are behind a trusted token or equivalent access control layer
- dead-letter handling is monitored for failed callback or processing events
- all provider payload validators are tested against the provider sandbox
- service-level alerts are configured for reconciliation breakage and payout failures

This keeps the system aligned with the premium operational position described in the broader documentation set.
