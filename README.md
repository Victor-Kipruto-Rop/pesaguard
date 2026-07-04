# PesaGuard

PesaGuard is a premium reconciliation and anomaly-detection platform for businesses accepting M-Pesa payments.

## What is included
- Webhook receiver with payload validation and durable idempotency
- Kafka-backed event flow for reconciliation
- Connector abstraction for Postgres, REST, and Google Sheets
- Modern dashboard shell and discrepancy management API
- Structured logging, health checks, CI, and a load test harness

## Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements_3.txt
pytest -q
```

## Next steps
- Connect the connector to a real tenant ledger
- Swap the dashboard shell for a full React/Next.js app if you want a production-grade frontend experience
- Wire SMS alerts and real operational metrics into the notifier and dashboard APIs
