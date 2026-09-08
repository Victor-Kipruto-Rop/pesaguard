# Communications Runbook

## Provider outage
Confirm provider health and error/timeout rates. Disable only the affected communication route, preserve queued records, and keep financial processing enabled. Use a configured fallback only after validating recipient/channel compatibility. Record an incident and replay after recovery.

## Queue backlog/high latency
Check worker count, database locks, lease expiry, Redis/Kafka dependencies, and provider rate limits. Increase workers only within provider/database limits. Do not create duplicate sends by manually re-enqueuing rows with active leases.

## Webhook failures
Check edge HTTPS, secret configuration, request size, signature header, and provider event IDs. Repair configuration, then replay authenticated inbox records through an audited admin action.

## Low balance
Confirm provider wallet and burn rate, notify the responsible operator, and apply the tenant/provider safety policy. Never silently mark a message delivered.

## Credential rotation
Create and validate the new secret in sandbox, deploy through the secret manager, verify one controlled send and callback, then revoke the old credential. Audit the operator and result.

## Campaign or OTP incident
Pause the persisted campaign or apply the account/IP/recipient block. Preserve audit and security evidence, notify incident response, and do not expose OTP values in logs or responses.
