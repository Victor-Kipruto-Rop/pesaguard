# Africa's Talking

`AfricasTalkingProvider` adapts the existing bounded-timeout SMS client to the provider-neutral contract. Provider acceptance is recorded as `accepted`; it is not delivery. `DELIVERED` is assigned only from an authenticated provider callback.

The canonical secret is `AFRICASTALKING_WEBHOOK_SECRET`. Runtime compatibility also accepts the historical `AFRICAS_TALKING_WEBHOOK_SECRET`. Rotate credentials through the secret manager and test sandbox delivery before production rollout.
