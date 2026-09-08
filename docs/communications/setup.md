# Communications Setup

## Prerequisites

- Python 3.10+
- PostgreSQL 13+ (recommended) or SQLite for development
- Kafka (optional, for event-driven ingestion)
- Redis (optional, for caching)

## Installation

1. Apply migrations with `alembic upgrade head`.
2. Configure environment variables (see below).
3. Register webhook endpoints with providers.
4. Run the communications worker separately from financial transaction workers.

## Environment Variables

### Africa's Talking (SMS)
| Variable | Required | Description |
|----------|----------|-------------|
| `AFRICASTALKING_USERNAME` | Yes | API username |
| `AFRICASTALKING_API_KEY` | Yes | API key |
| `AFRICASTALKING_ENVIRONMENT` | Yes | `sandbox` or `production` |
| `AFRICASTALKING_SENDER_ID` | No | Default sender ID |
| `AFRICASTALKING_SHORTCODE` | No | Default shortcode |
| `AFRICASTALKING_CALLBACK_BASE_URL` | Yes | Base URL for delivery callbacks |
| `AFRICASTALKING_WEBHOOK_SECRET` | Yes | HMAC verification secret |
| `AFRICASTALKING_TIMEOUT_SECONDS` | No | Request timeout (default: 10) |
| `AFRICASTALKING_MAX_RETRIES` | No | Max transport retries (default: 5) |

### Email (SMTP)
| Variable | Required | Description |
|----------|----------|-------------|
| `PESAGUARD_SMTP_HOST` | Yes | SMTP server hostname |
| `PESAGUARD_SMTP_PORT` | Yes | SMTP server port |
| `PESAGUARD_SMTP_USERNAME` | Yes | SMTP username |
| `PESAGUARD_SMTP_PASSWORD` | Yes | SMTP password |
| `PESAGUARD_SMTP_FROM_EMAIL` | Yes | Default sender email |

### Worker Configuration
| Variable | Default | Description |
|----------|---------|-------------|
| `PESAGUARD_COMMUNICATION_RETRY_BASE_SECONDS` | 5 | Base backoff delay |
| `PESAGUARD_COMMUNICATION_RETRY_MAX_SECONDS` | 600 | Maximum backoff delay |
| `PESAGUARD_COMMUNICATION_RETRY_JITTER` | 0.25 | Jitter ratio (0-1) |
| `PESAGUARD_OUTBOX_POLL_SECONDS` | 5 | Worker poll interval |
| `PESAGUARD_COMMUNICATION_PROVIDER_RATE_PER_MINUTE` | 0 | Rate limit (0=unlimited) |

### Policy Configuration
| Variable | Default | Description |
|----------|---------|-------------|
| `PESAGUARD_COMMUNICATION_POLICY_DEFAULTS` | (empty) | JSON overrides for policy thresholds |
| `PESAGUARD_COMMUNICATION_SLA_TARGETS` | (empty) | JSON overrides for SLA targets by priority |
| `PESAGUARD_COMMUNICATION_UNIT_COSTS` | (empty) | JSON overrides for per-channel costs |
| `PESAGUARD_COMMUNICATION_WALLET_BALANCE` | (empty) | Provider balance for runway calculation |

### OTP Configuration
| Variable | Default | Description |
|----------|---------|-------------|
| `PESAGUARD_OTP_TTL_SECONDS` | 300 | OTP validity period |
| `PESAGUARD_OTP_MAX_ATTEMPTS` | 5 | Max verification attempts |
| `PESAGUARD_OTP_RESEND_COOLDOWN_SECONDS` | 60 | Minimum time between resends |
| `PESAGUARD_OTP_RECIPIENT_HOURLY_LIMIT` | 5 | Max OTPs per recipient per hour |
| `PESAGUARD_OTP_IP_HOURLY_LIMIT` | 20 | Max OTPs per IP per hour |
| `PESAGUARD_OTP_HASH_PEPPER` | (empty) | Pepper for OTP hash (required in production) |

### Feature Flags
| Variable | Default | Description |
|----------|---------|-------------|
| `PESAGUARD_FLAG_AFRICASTALKING_SMS` | true | Enable Africa's Talking SMS |
| `PESAGUARD_FLAG_AFRICASTALKING_USSD` | false | Enable USSD |
| `PESAGUARD_FLAG_AFRICASTALKING_VOICE` | false | Enable voice |
| `PESAGUARD_FLAG_AFRICASTALKING_WHATSAPP` | false | Enable WhatsApp |
| `PESAGUARD_FLAG_PROVIDER_FAILOVER` | true | Enable provider failover |
| `PESAGUARD_FLAG_SMART_ROUTING` | true | Enable smart routing |
| `PESAGUARD_FLAG_AI_COMMUNICATIONS` | false | Enable AI operations assistant |
| `PESAGUARD_FLAG_CAMPAIGNS` | true | Enable campaigns |
| `PESAGUARD_FLAG_BULK_SMS` | true | Enable bulk SMS |

## Webhook Registration

Register `/api/v1/webhooks/africastalking/delivery` with Africa's Talking. Require HTTPS at the edge. The endpoint verifies HMAC-SHA256 signatures using `AFRICASTALKING_WEBHOOK_SECRET`.

## Running the Worker

```bash
python -m pesaguard_backend_pipeline.communications.worker
```

Run separately from financial transaction workers. Scale horizontally by running multiple worker instances (leases prevent duplicate processing).

## Security Notes

- Use sandbox credentials outside production
- Never place provider keys in source, logs, notification bodies, or frontend bundles
- Configure `PESAGUARD_OTP_HASH_PEPPER` in production (without it, OTPs use a deterministic dev fallback)
- Rotate credentials through the secret manager
- Test sandbox delivery before production rollout
