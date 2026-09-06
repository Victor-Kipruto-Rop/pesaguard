# PesaGuard 🛡️ Multi-Rail Reconciliation & Payment Control Platform

PesaGuard is the financial operations backbone for modern payment ecosystems. It brings M-Pesa, Airtel Money, and bank transfer flows into one real-time reconciliation, alerting, and payout orchestration platform designed for teams that cannot tolerate silent mismatches, duplicate webhook replays, or weak operational auditability.

Built for finance teams, treasury teams, SACCOs, fintechs, lenders, insurers, and merchants operating in fast-moving, multi-rail transaction environments.

---

## Why this platform exists

Most payment operations still depend on fragmented tools: spreadsheets, bank statements, wallet reports, and manual comparisons. That creates risk across the entire payment lifecyle:

- duplicate callbacks and replayed transactions
- mismatched ledger entries across provider and internal books
- late detection of failed or suspicious payouts
- weak accountability during exceptions and disputes
- slow, manual reconciliation for every settlement cycle

PesaGuard replaces that fragmentation with an auditable, provider-aware operational control layer.

---

## Platform capabilities

- Reconciliation across M-Pesa, Airtel Money, and bank transfer rails
- Provider-aware validation and normalization for each payment gateway
- Idempotent webhook ingestion to prevent double-processing
- Duplicate detection and resilient dead-letter handling
- Outbound payment request helpers for provider-controlled disbursements
- Tenant-scoped provider configuration and admin-facing operational routes
- Real-time anomaly detection and reconciliation reporting for finance operations
- Production-oriented backend patterns with Kafka, Redis, PostgreSQL, and dockerized deployment support

---

## Supported rails

| Rail | Status | Coverage |
|---|---|---|
| M-Pesa / Daraja | Production-ready | Webhook ingestion, validation, normalization, reconciliation |
| Airtel Money | Production-ready | Auth flow, config, callback validation, outbound payout helper |
| Bank transfers | Integrated | Transfer request flow, tenant credentials, normalization, ingestion support |
| Additional providers | Extensible | Provider abstraction is ready for follow-on expansion |

---

## Business value

### Finance teams
- reduce unreconciled payment exposure
- accelerate settlement review and ledger confidence
- audit every payment event from gateway to internal state

### Operations teams
- detect issues before they become customer-facing incidents
- respond to payment exceptions with clear provider context
- reduce manual investigations and spreadsheet-driven error handling

### Risk and compliance teams
- keep provider-level transaction trails in one place
- identify suspicious activity earlier through consistent normalization
- maintain clearer controls over payout and webhook processing

---

## Architecture overview

PesaGuard is structured around a tenant-aware, webhook-first backend model:

- incoming provider callbacks are validated and normalized
- a reconciliation engine matches transaction patterns against ledger and settlement states
- idempotent event storage prevents duplicate processing across retries
- admin routes expose operational actions for provider-specific payouts and ingestion tasks
- alerting and monitoring layers surface operational drift for finance teams

### Bank reconciliation flow

```mermaid
flowchart TD
    A[M-Pesa] --> N[Normalization]
    B[Airtel Money] --> N
    C[Bank] --> N
    D[Future Providers] --> N

    N --> R[Reconciliation Engine]

    R --> M[Matched]
    R --> E[Exceptions]
    R --> U[Unmatched]

    E --> S[Settlement Engine]
    U --> S
    M --> S
```

This advanced flow is the operational heart of the platform: raw payment events from multiple rails are normalized into one canonical model, evaluated against internal ledger records, and then partitioned into matched, exceptional, or unmatched results before settlement or follow-up handling.

---

## Quick start

```bash
git clone https://github.com/Victor-Kipruto-Rop/pesaguard.git
cd pesaguard
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Configure the environment for your tenant and provider setup:

- `DATABASE_URL`
- `TENANT_ID`
- `DARAJA_*` credentials
- `AIRTEL_*` credentials
- `BANK_*` credentials
- `REDIS_URL` and optional Kafka settings

See the setup and API docs for production deployment guidance.

---

## Documentation index

- [docs/SETUP.md](docs/SETUP.md)
- [docs/FEATURES.md](docs/FEATURES.md)
- [docs/PRODUCT_SCOPE.md](docs/PRODUCT_SCOPE.md)
- [docs/ADMIN_API.md](docs/ADMIN_API.md)
- [docs/AIRTEL_MONEY_INTEGRATION.md](docs/AIRTEL_MONEY_INTEGRATION.md)

---

## Admin API at a glance

The backend exposes provider-aware admin endpoints for payouts and ingestion flows:

| Area | Endpoint | Purpose |
|---|---|---|
| M-Pesa | `POST /webhook/mpesa/validation` | Validation callback response |
| M-Pesa | `POST /webhook/mpesa/confirmation` | Confirmation callback ingestion |
| Airtel | `POST /admin/airtel/payments` | Trigger Airtel outbound payout |
| Airtel | `GET /admin/airtel/payments/contracts` | Contract examples and validation notes |
| Bank | `POST /admin/bank/payments` | Trigger bank transfer payout |
| Bank | `GET /admin/bank/payments/contracts` | Contract examples and validation notes |
| Bank | `POST /admin/bank/ingest` | Ingest CSV, Excel, PDF, webhooks, SFTP, API records |
| Bank | `GET /admin/bank/ingest/contracts` | Statement ingestion contract examples |

These endpoints are designed to be admin-authenticated and tenant-scoped for real operational use rather than demo-only plumbing.

---

## Example environment settings

```env
DATABASE_URL=postgresql://pesaguard:pesaguard@localhost:5432/pesaguard
TENANT_ID=default
REDIS_URL=redis://localhost:6379/0
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
PESAGUARD_ADMIN_API_TOKEN=your-admin-token
```

---

## Deployment posture

PesaGuard is designed to be operationally practical in real-world finance environments:

- PostgreSQL-compatible persistence
- SQLite-safe local and test execution
- Docker-friendly deployment patterns
- Redis-backed operational caching and idempotency support
- Kafka-based downstream event publication
- tenant-scoped provider configuration for multi-client deployments

---

## Roadmap

- [x] M-Pesa reconciliation foundation
- [x] Airtel Money provider integration
- [x] Bank transfer provider integration
- [x] Provider-aware reconciliation across all three rails
- [x] Outbound payout helpers and admin route wiring
- [x] Multi-source bank statement ingestion support
- [x] Standardized admin API contract documentation
- [ ] Additional customer-specific operational workflow expansion

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

## Contact

Built for serious financial operations teams in East Africa and beyond.

For pilot conversations, integration requests, or production deployment discussion, reach out through the repository owner and implementation channels.
