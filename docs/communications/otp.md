# OTP Security

## Overview

The OTP (One-Time Password) system provides cryptographically secure verification codes for sensitive operations. It includes abuse detection, rate limiting, and risk-based policies.

## OTP Lifecycle

```
Request OTP
    │
    ▼
┌─────────────────┐
│ Rate Limits OK? │──No──> Reject (OtpRateLimited)
└─────────────────┘
    │ Yes
    ▼
┌─────────────────┐
│ Cooldown OK?    │──No──> Reject (resend_cooldown)
└─────────────────┘
    │ Yes
    ▼
Generate 6-digit code (secrets.choice)
    │
    ▼
Store SHA-256(code + pepper) → communication_otp_challenges
    │
    ▼
Send via policy-determined channel (SMS/email)
    │
    ▼
User submits code
    │
    ▼
┌─────────────────┐
│ Valid attempt?  │──No──> Increment attempts, reject
└─────────────────┘
    │ Yes
    ▼
Compare hash (hmac.compare_digest)
    │
    ▼
Mark consumed → Success
```

## Security Controls

### Generation
- Uses `secrets.choice()` (cryptographically secure RNG)
- 6 digits (1,000,000 possible codes)
- Configurable length for elevated risk

### Storage
- Only the hash is stored (never plaintext)
- SHA-256 with configurable pepper
- Pepper via `PESAGUARD_OTP_HASH_PEPPER` env var
- Deterministic dev fallback if pepper not set (production must configure)

### Rate Limits

| Limit | Default | Env Variable |
|-------|---------|--------------|
| Resend cooldown | 60 seconds | `PESAGUARD_OTP_RESEND_COOLDOWN_SECONDS` |
| Max attempts | 5 | `PESAGUARD_OTP_MAX_ATTEMPTS` |
| Recipient hourly | 5 | `PESAGUARD_OTP_RECIPIENT_HOURLY_LIMIT` |
| IP hourly | 20 | `PESAGUARD_OTP_IP_HOURLY_LIMIT` |
| Elevated cooldown | 120 seconds | `PESAGUARD_OTP_ELEVATED_COOLDOWN_SECONDS` |

### Risk-Based Policy

| Risk Level | TTL | Max Attempts | Cooldown |
|------------|-----|--------------|----------|
| Normal | 300s | 5 | 60s |
| Elevated | 120s | 3 | 120s |

Elevated risk is triggered by suspicious login patterns (detected by the fraud engine).

## Abuse Detection

The anomaly detection system identifies OTP abuse patterns:

### Recipient Flood
Many OTPs to the same recipient in a short window.

```json
{
  "type": "otp_flood_same_recipient",
  "recipient": "+254700000001",
  "requests": 7,
  "limit": 5,
  "recommended_actions": ["rate_limit_recipient", "raise_security_incident"]
}
```

### IP Enumeration
Many OTPs to different recipients from the same IP.

```json
{
  "type": "otp_enumeration_same_ip",
  "ip_address": "203.0.113.9",
  "requests": 25,
  "distinct_recipients": 25,
  "limit": 20,
  "recommended_actions": ["rate_limit_ip", "temporary_block", "raise_security_incident"]
}
```

## API Usage

### Issue OTP
```python
from pesaguard_backend_pipeline.communications.domain import issue_otp

challenge, code = issue_otp(
    session,
    tenant_id="tenant-a",
    recipient="+254700000001",
    purpose="login",
    ip_address="203.0.113.9",
    risk_level="normal",  # or "elevated"
)
# Send `code` to user via SMS/email
```

### Verify OTP
```python
from pesaguard_backend_pipeline.communications.domain import verify_otp

is_valid = verify_otp(session, challenge, user_submitted_code)
if is_valid:
    # Proceed with sensitive operation
    pass
```

## Configuration

Required environment variables for production:

```bash
# Required in production (without this, uses deterministic dev fallback)
export PESAGUARD_OTP_HASH_PEPPER="$(openssl rand -hex 32)"

# Optional tuning
export PESAGUARD_OTP_TTL_SECONDS=300
export PESAGUARD_OTP_MAX_ATTEMPTS=5
export PESAGUARD_OTP_RESEND_COOLDOWN_SECONDS=60
export PESAGUARD_OTP_RECIPIENT_HOURLY_LIMIT=5
export PESAGUARD_OTP_IP_HOURLY_LIMIT=20
```

## Security Best Practices

1. **Always configure pepper in production** - Without it, OTP hashes use a deterministic dev fallback
2. **Never log OTP values** - Only log challenge IDs and metadata
3. **Use elevated risk for suspicious contexts** - Integrate with fraud engine
4. **Monitor abuse patterns** - Set up alerts for flood/enumeration detection
5. **Rotate pepper periodically** - Invalidate old challenges on rotation
6. **Enforce HTTPS** - OTPs must never travel over plaintext