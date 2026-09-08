# Communications Security

Tenant identity is derived from authenticated principals for API sends; webhook tenant identity is derived from the stored notification. Idempotency keys and provider event uniqueness prevent duplicate processing. Provider credentials are environment/secret-store values.

Required production controls: HTTPS termination, secret rotation, strict RBAC for provider configuration and replay, request size/rate limits, masked structured logs, dependency/container scanning, and tests for IDOR, tenant isolation, webhook forgery/replay, OTP abuse, and rate-limit bypass.
