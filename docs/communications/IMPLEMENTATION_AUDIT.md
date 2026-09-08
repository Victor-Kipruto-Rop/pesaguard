# Communications Implementation Audit

Date: 2026-09-08
Scope: Africa's Talking, communications package, legacy alerting, delivery webhooks, persistence, workers, security, operations, frontend, and tests.

## Executive Summary

The repository contains a useful communications foundation: provider-neutral request contracts, Africa's Talking transport code, durable notification/outbox tables, delivery reports, HMAC webhook verification, tenant-scoped idempotency, and focused unit tests. It is not yet a production-ready enterprise communications platform because the new outbox architecture and legacy alerting architecture are both active, lifecycle transitions are not centrally enforced, provider errors are not consistently classified, and several advertised capabilities are persistence-only or not wired into runtime workers.

Financial processing is not intentionally coupled to provider delivery in the reviewed communication routes, but the legacy alerting path and broad exception handling make operational behavior inconsistent. The communication subsystem should fail independently, with explicit retry/dead-letter behavior and auditable state transitions.

## Component Audit

| Feature | Current State | Production Ready? | Problems | Risk | Recommended Improvement |
|---|---|---:|---|---|---|
| Provider-neutral contracts | PARTIAL | No | `CommunicationProvider`, request, and response contracts exist, but runtime routing is effectively SMS/Africa's Talking only. | High | Wire provider routing and channel capability checks through all send paths. |
| Africa's Talking transport | COMPLETE | With conditions | The legacy client has validation, bounded transport retries, timeouts, and response normalization. | Medium | Keep as transport adapter; expose standardized error categories and metrics. |
| Africa's Talking adapter | PARTIAL | No | Adapter maps only a few outcomes and can collapse provider rejection details into `PROVIDER_REJECTED`. | High | Map provider HTTP/API responses to internal error categories and preserve safe diagnostic metadata. |
| Legacy notifier | NEEDS HARDENING | No | `notifier.py` remains used by alerting; non-throwing `skipped`/failed results can be treated as success. | Critical | Route operational notifications through the durable notification service or make the legacy path explicitly test-only. |
| Notification API | PARTIAL | No | `/api/v1/communications/sms` queues messages and is tenant-scoped, but accepts raw message bodies and has limited policy enforcement. | High | Add approved-template/policy evaluation, quotas, structured errors, and route-level tests. |
| Notification lifecycle | PARTIAL | No | Status values exist, but service, worker, and webhook assign strings directly without a shared transition validator. | Critical | Centralize valid transitions and reject stale/out-of-order updates. |
| Durable outbox | PARTIAL | No | Leasing and dead-letter persistence exist; retry handling is broad and backoff is fixed/raw. | Critical | Classify errors before retry, use bounded configurable exponential backoff with jitter, and emit transition events. |
| Worker | PARTIAL | No | Outbox polling works, but every exception is retried, provider selection is factory-fixed, and worker integration is lightly tested. | Critical | Handle permanent failures immediately, expose queue metrics, and test lease/recovery/concurrency. |
| Provider routing/failover | MOCKED | No | Router has an in-memory failure counter but is not injected into routes/workers/factory; no explicit CLOSED/OPEN/HALF_OPEN model. | High | Persist/configure provider priority and implement an explicit circuit breaker with health metrics. |
| Delivery reports | PARTIAL | No | Reports and provider-message lookup exist; delivery status mapping is narrow and can overwrite terminal states. | High | Enforce monotonic terminal transitions and store normalized error/category/timestamps. |
| Delivery webhooks | BROKEN / NEEDS HARDENING | No | HMAC verification exists, but no timestamp/replay window, schema gate, request authentication beyond signature, or async inbox queue. Secret naming differs between code and documented environment configuration. | Critical | Validate timestamp/replay/schema, persist a minimal inbox record, enqueue processing, and return quickly. |
| Webhook inbox/idempotency | PARTIAL | No | `CommunicationWebhookEvent` is an inbox-like table with a uniqueness key, but payload is stored in plaintext and processing is synchronous. | High | Add payload hash, processing state transitions, redacted storage/logging, and replay permissions/audit. |
| Internal event sourcing | PARTIAL | No | Event builders exist and a Kafka consumer function exists, but the consumer is not clearly started in deployment and notification lifecycle events are incomplete. | High | Define versioned event names and publish lifecycle events from one transition service. |
| Business-event decoupling | BROKEN / PARTIAL | No | Reconciliation still reaches legacy alerting/RQ flows while the newer notification event path is separate. | Critical | Publish domain events; let the notification policy engine decide channels/providers. |
| Templates | PARTIAL | No | Template persistence exists, but raw messages are accepted and approval/version enforcement is incomplete. | Medium | Require approved versions for governed notification types and validate variables. |
| Preferences/consent | PARTIAL | No | Basic preferences and marketing consent checks exist only for some paths; consent lacks full immutable history/version/status model. | High | Add purpose-specific consent events and apply policy consistently to all channels. |
| OTP | MOCKED | No | OTP challenges are stored/hashed, but the generated code is not sent through the durable notification path. | Critical | Enqueue the OTP through the communication service and add abuse controls, cooldown, and audit coverage. |
| Campaigns | MOCKED | No | Campaign persistence and expansion code exist, but scheduling/worker execution is not wired. | High | Add an explicit campaign scheduler/worker with streaming recipient batches and pause/resume/cancel state validation. |
| Cost/billing readiness | PARTIAL | No | Provider routes include a cost limit field, but per-message segment/unit/total cost ledger and forecasting are absent. | Medium | Add immutable usage/cost records and tenant-period aggregation. |
| Incident/anomaly management | MISSING | No | Existing general monitoring is not a communication-specific incident or anomaly workflow. | Medium | Add golden-signal metrics, alert fingerprints, incidents, and provider-health dashboards. |
| Authentication/RBAC | PARTIAL | No | Communication send route uses permission checks; privileged replay/provider/campaign operations are not comprehensively exposed or tested. | High | Add explicit permissions, tenant scoping, step-up MFA, and audit records for dangerous actions. |
| Observability | PARTIAL | No | Logging and general metrics exist; trace/correlation fields are present on notifications but not consistently propagated. | High | Add structured lifecycle logs, provider latency/error metrics, queue depth/lag, and webhook health. |
| Database/migrations | PARTIAL | No | Foundation/outbox/product migrations exist and are ordered; some runtime paths use `create_all()` and migration validation is not a CI gate. | High | Require Alembic in deployment/CI and test PostgreSQL migration upgrades. |
| Redis/Kafka/queues | PARTIAL | No | Infrastructure and producer abstractions exist; communication Kafka consumption and backpressure behavior are not fully wired or verified. | High | Document topics/keys, start consumers explicitly, and test outage recovery. |
| Frontend/dashboard | PARTIAL | No | Existing frontend/dashboard surfaces exist, but a communications command center, message timeline, provider health, and safe admin actions are not complete. | Medium | Add tenant-scoped operational views with pagination and RBAC-aware actions. |
| Docker/deployment | PARTIAL | No | Compose includes a worker in one stack, but full-stack worker/configuration coverage is inconsistent. | High | Make worker and consumer deployment explicit in every production topology. |
| CI/CD/security testing | NEEDS HARDENING | No | Pytest runs, but migration, route/worker integration, dependency/container/secret scans, and communication chaos tests are not complete gates. | High | Add focused communication gates and security tests before production rollout. |
| Documentation/runbooks | PARTIAL | No | General architecture and operations docs exist; communications-specific audit/runbook/readiness docs were missing or stale. | Medium | Maintain communications architecture, setup, provider, webhook, security, DR, and outage runbooks. |

## Fake or Incomplete Production Behavior Found

- Legacy SMS alerting can treat a non-exception provider response as success without checking provider status.
- Product capability rows for OTP and campaigns exist without a complete delivery/scheduling runtime path.
- Provider failover is implemented as an isolated in-memory router rather than a production routing service.
- The Kafka notification consumer is defined but not shown as a required running deployment process.
- Delivery webhooks process business state synchronously and do not yet have replay/timestamp protections.
- The newer notification model has lifecycle values, but no common transition gate prevents invalid or out-of-order updates.

## Immediate Priorities

1. Enforce one lifecycle state machine and classify retryable versus permanent errors.
2. Disable or migrate legacy alerting sends so financial workflows never depend on two competing communication paths.
3. Harden webhook authentication, replay protection, inbox persistence, and asynchronous processing.
4. Wire provider routing/circuit health and make worker behavior observable.
5. Add migration, worker, route, concurrency, and end-to-end tests before claiming production readiness.

## Readiness Conclusion

Current communications readiness: **PARTIAL / NOT PRODUCTION READY**. The foundation is valuable, but the requested 90% enterprise target is not supported by the current implementation evidence. A scored readiness assessment and remediation plan belong in `docs/communications/PRODUCTION_READINESS.md` after the hardening work and full test run.
