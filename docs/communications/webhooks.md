# Delivery Webhooks

The delivery endpoint limits request size, verifies HMAC-SHA256 using the configured secret, validates JSON/object shape, resolves the notification by provider message ID, and deduplicates provider event IDs. Duplicate callbacks return a duplicate result and do not create another delivery report.

The current endpoint performs persistence in the request path. A future inbox worker should separate receipt from processing, add timestamp/replay-window validation, hash/redact stored payloads, and expose privileged replay with audit logging.
