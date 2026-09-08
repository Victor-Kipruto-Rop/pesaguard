# Communications Security

## Overview

Communications security protects PesaGuard's messaging infrastructure against forgery, replay, abuse, and tenant data leakage. Security is layered: transport security, authentication, authorization, input validation, and rate limiting.

## Authentication

### API Authentication
- All communication API endpoints require JWT bearer tokens
- Permission-scoped: `read:communications`, `send:communications`, `manage:communications`
- Tenant identity derived from authenticated principal (never from request body)

### Webhook Authentication
- HMAC-SHA256 signature verification using `AFRICASTALKING_WEBHOOK_SECRET`
- Legacy alias accepted: `AFRICAS_TALKING_WEBHOOK_SECRET`
- Constant-time comparison via `hmac.compare_digest`

## Authorization (RBAC)

| Permission | Description |
|------------|-------------|
| `read:communications` | View messages, analytics, health |
| `send:communications` | Send notifications, create campaigns |
| `manage:communications` | Admin actions: replay, quotas, provider config |

### Privileged Actions (require `manage:communications`)
- Webhook replay
- Dead-letter replay
- Campaign pause/resume/cancel
- Tenant quota changes
- Incident status transitions

## Tenant Isolation

- All queries are scoped by `tenant_id` derived from the authenticated principal
- Webhook callbacks derive tenant from the stored notification (never from payload)
- Saved filters, quotas, templates, preferences are all tenant-scoped
- Unique constraints enforce `(tenant_id, idempotency_key)` for deduplication

## Input Validation

| Layer | Control |
|-------|---------|
| JSON schema | Must be an object; required fields validated |
| Recipient | Phone/email format validation per channel |
| Message | Length and content checks |
| Webhook payload | Provider event ID and message ID required |
| Request size | `PESAGUARD_WEBHOOK_MAX_BODY_BYTES` limit |

## Replay Protection

- Webhook timestamps validated against a 5-minute (default) window
- Future-skip tolerance: 60 seconds
- Duplicate events rejected by unique `(provider, provider_event_id, event_type)` constraint

## OTP Security

| Control | Implementation |
|---------|----------------|
| Generation | `secrets.choice()` (cryptographically secure) |
| Storage | SHA-256 + pepper (never plaintext) |
| Cooldown | `PESAGUARD_OTP_RESEND_COOLDOWN_SECONDS` (default 60) |
| Attempt limits | `PESAGUARD_OTP_MAX_ATTEMPTS` (default 5) |
| Rate limits | Per-recipient and per-IP hourly caps |
| Risk-based | Elevated risk = shorter TTL, fewer attempts |

## Rate Limiting

- **Provider rate governor**: Token-bucket per provider (`PESAGUARD_COMMUNICATION_PROVIDER_RATE_PER_MINUTE`)
- **Queue backpressure**: Automatic slowdown when queue exceeds depth
- **OTP rate limits**: Per-recipient, per-IP hourly caps
- **Campaign rate limits**: `rate_per_minute` per campaign

## Secrets Management

| Secret | Storage |
|--------|---------|
| `AFRICASTALKING_API_KEY` | Environment / secret store |
| `AFRICASTALKING_WEBHOOK_SECRET` | Environment / secret store |
| `PESAGUARD_OTP_HASH_PEPPER` | Secret store (required production) |
| SMTP credentials | Secret store |

## Security Testing

Required before production:

1. **SAST** - Static analysis (Bandit, Semgrep)
2. **Dependency scanning** - OWASP Dependency Check
3. **Secret scanning** - TruffleHog, git-secrets
4. **Container scanning** - Trivy
5. **API security** - OWASP ZAP
6. **RBAC testing** - Permission boundaries
7. **Tenant isolation** - Cross-tenant access attempts
8. **Rate-limit testing** - Brute-force prevention
9. **Webhook replay testing** - Timestamp manipulation
10. **OTP abuse testing** - Flood/enumeration patterns

## Incident Response

Security incidents create `communication_incidents` records automatically:

- OTP flood detection → `high` severity incident
- OTP IP enumeration → `critical` severity incident
- Repeated provider auth failures → `high` severity incident
- SLA breaches → `medium`/`high` severity incident

## Audit

All privileged operations should be audited:

- Webhook replay (actor, event, timestamp)
- Dead-letter replay (actor, entry, timestamp)
- Campaign cancellation (actor, campaign)
- Quota changes (actor, scope, old/new values)
