# Communications Platform Implementation Summary

## Scope Delivered

This increment establishes the production foundation for a provider-independent communications platform without replacing the existing PesaGuard alerting path.

### Architecture Changes

- Added `pesaguard_backend_pipeline/communications/` with provider-neutral channels, priorities, notification states, request/result contracts, errors, provider adapters, notification service, models, and webhook processing.
- Added `AfricasTalkingProvider`, which wraps the existing robust SMS client rather than spreading provider calls through business services.
- Added tenant-scoped notification idempotency and provider-attempt persistence.
- Added authenticated and idempotent delivery callback processing.
- Registered the delivery endpoint with the existing Flask dashboard service.
- Added authenticated tenant-scoped SMS submission at `POST /api/v1/communications/sms`.
- Added structured notification events for reconciliation and fraud/security-compatible workflows.
- Added `notification.events`, `notification.status`, and `communication.audit` Kafka topic definitions.
- Moved reconciliation alert dispatch behind the existing RQ worker boundary; reconciliation no longer calls communication providers directly.

### Files Created

- `CURRENT_ARCHITECTURE.md`
- `pesaguard_backend_pipeline/communications/`
- `pesaguard_backend_pipeline/test_communications.py`
- `alembic/versions/20260908_add_communications_foundation.py`
- `pesaguard_backend_pipeline/communications/events.py`
- `pesaguard_backend_pipeline/communications/routes.py`

### Files Modified

- `alembic/env.py`
- `pesaguard_backend_pipeline/action_audit.py` and its existing tests from the preceding audit-integrity increment
- `pesaguard_backend_pipeline/app_2.py`
- `pesaguard_backend_pipeline/background_tasks.py`
- `pesaguard_backend_pipeline/reconciliation_job.py`
- `pesaguard_backend_pipeline/topics.py`
- `pesaguard_backend_pipeline/auth_rbac.py`
- `pesaguard_backend_pipeline/africas_talking.py`
- `.env.example`

## Persistence

The migration `20260908_add_communications_foundation` adds:

- `communication_notifications`
- `communication_attempts`
- `communication_delivery_reports`
- `communication_webhook_events`

Constraints include tenant/idempotency uniqueness, provider event uniqueness, lifecycle checks, foreign keys, and query indexes. The migration is currently the Alembic head.

## API Endpoint

- `POST /api/v1/webhooks/africastalking/delivery`
- `POST /api/v1/communications/sms`

The endpoint requires `X-Africa-Talking-Signature` or `X-Webhook-Signature`, verifies HMAC-SHA256 using `AFRICASTALKING_WEBHOOK_SECRET`, enforces the configured body limit, processes duplicate callbacks safely, and returns standardized JSON errors.

The SMS endpoint requires JWT permission `send:communications`, derives tenant identity from the authenticated principal, requires an idempotency key, and persists/submits through `NotificationService` and the provider abstraction.

## Kafka and Redis

Kafka topic definitions now include `notification.events`, `notification.status`, and `communication.audit`. Existing Kafka/RQ/Redis infrastructure remains in use; no second queue or event system was introduced. Reconciliation queues notification events through RQ, and the worker uses the legacy alerting service as a compatibility adapter until channel-specific notification workers are migrated.

## Environment Variables

`.env.example` now documents placeholder-only values for:

- `AFRICASTALKING_USERNAME`
- `AFRICASTALKING_API_KEY`
- `AFRICASTALKING_ENVIRONMENT`
- `AFRICASTALKING_SENDER_ID`
- `AFRICASTALKING_SHORTCODE`
- `AFRICASTALKING_CALLBACK_BASE_URL`
- `AFRICASTALKING_WEBHOOK_SECRET`
- `AFRICASTALKING_TIMEOUT_SECONDS`
- `AFRICASTALKING_MAX_RETRIES`

The SMS client accepts both these canonical names and the existing `AFRICAS_TALKING_*`/`AT_ENVIRONMENT` names.

## Security

- Provider credentials remain environment-driven.
- Webhook callbacks require HMAC verification.
- Delivery callback records derive tenant identity from the stored notification, not untrusted webhook fields.
- Duplicate callbacks are rejected by application lookup and database uniqueness constraints.
- Notification sends require a tenant-scoped idempotency key.
- Existing audit, RBAC, rate limiting, and correlation-ID systems remain available for the next integration slice.

## Testing

Validated locally:

- Communications foundation/provider/webhook tests: 5 passed.
- Communications event integration tests: 7 passed.
- Reconciliation regression tests: 13 passed.
- Combined communications, dashboard, and reconciliation regression slice: 14 passed.
- Communications plus existing notifier and audit tests: 22 passed.
- Existing dashboard provider regression test: passed with the communications route registered.
- Changed Python files compile successfully.
- `git diff --check` passes.
- Alembic reports `20260908_add_communications_foundation` as the current head.

## Deployment and Rollback

Before deployment:

1. Set the Africa's Talking sandbox credentials and webhook secret in the deployment secret store.
2. Set the callback URL to `/api/v1/webhooks/africastalking/delivery`.
3. Run `alembic upgrade head` against the target database.
4. Keep the existing alerting path enabled until the outbox worker and business-event adapters are deployed.

Rollback is the normal Alembic downgrade for the communications foundation migration. Do not downgrade after production communication records have been created without an approved data-retention/export procedure.

## Known Limitations and Next Steps

This is not the full enterprise communications roadmap. The following are intentionally not yet delivered: durable communication outbox leasing, bulk/scheduled campaigns, template/version management, OTP/MFA, preferences/consent/quiet hours, provider failover, cost/wallet analytics, USSD, voice, WhatsApp, frontend dashboard, full transaction/fraud event adapters, and end-to-end provider tests. These should be implemented behind the contracts added here and feature flags where appropriate.
