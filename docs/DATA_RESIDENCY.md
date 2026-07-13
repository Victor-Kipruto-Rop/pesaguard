# Data Residency Decision

## Current position

PesaGuard is currently documented as a pilot-stage SaaS workflow for reconciliation and anomaly detection. The initial deployment posture should be treated as a decision that must be validated against the actual hosting provider and customer requirements.

## Storage locations and jurisdiction

- Primary application data: to be defined by the selected hosting provider and deployment environment.
- PostgreSQL data: to be stored in the deployment region selected for the production environment.
- Kafka / event streaming: to be stored in the same deployment region unless a specific compliance need requires a different arrangement.
- Backups: must inherit the same residency decision as the primary data store.
- Logs: should be retained in the same jurisdiction as the primary deployment unless a documented exception exists.

## Recommended approach

For pilot use, prefer a Kenya-based or East Africa-based deployment region if available from the selected provider. If a provider only offers a non-Kenya region, document the reason, legal basis, and any contractual or technical mitigation before going live.

## Pending inputs

- The actual cloud provider and region used in production.
- Whether a specific pilot customer requires strict Kenya-local data residency.
- Whether any managed service is only available in a non-Kenya region.
