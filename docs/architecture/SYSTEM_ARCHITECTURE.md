# PesaGuard Architecture

PesaGuard is a Python Flask-based fintech reconciliation and transaction-processing repository. The implementation is centered in the `pesaguard_backend_pipeline` package and uses a collection of Flask app modules (`app.py`, `app_1.py`, `app_2.py`, `app_3_features.py`, `app_4_advanced_features.py`) plus worker, reconciliation, reporting, and notification helpers.

## Observed runtime architecture

- Web/API layer: Flask routes and webhook handlers in the Python package.
- Background workers: Redis/RQ task queue integration via `background_tasks.py` and workers in `alerting_consumer.py`, `communications/worker.py`, and similar modules.
- Data layer: SQLAlchemy and PostgreSQL, with SQLite used in tests and local development.
- Message/event layer: Kafka producers and topic utilities around `producer.py` and `topics.py`.
- Caching and throttling: Redis-backed rate limiting and RQ queue integration.
- Reconciliation and fraud/business logic: reconciliation engine, event store, discrepancy handling, and alerting services.
- External providers: Safaricom Daraja / M-Pesa webhook callback handling and Africa's Talking communication provider hooks.

## Repository structure

The primary backend package is `pesaguard_backend_pipeline/` and contains:

- Web API and route modules such as `app.py`, `app_2.py`, `app_3_features.py`, `app_4_advanced_features.py`.
- Data and model layers: `models.py`, `event_store.py`, `discrepancy_dao.py`, `action_audit.py`.
- Reconciliation and business services: `reconciliation_engine.py`, `reconciliation_job.py`, and supporting utilities.
- Security and access layers: `auth_rbac.py`, `rbac.py`, `security_helpers.py`.
- Messaging and queue features: `producer.py`, `background_tasks.py`, `rate_limiter.py`.
- Communication and notification services such as `email_service.py`, `africas_talking.py`, and `alerting_*` modules.

## Service boundaries

The observed service boundaries are intentionally kept loose and modular rather than being forced into a single monolith framework. Components are organized around transaction ingestion, normalization, reconciliation, fraud/anomaly handling, notifications, reporting, and configuration.

## Supported operating modes

The project supports local development, Docker-oriented deployment, and environment-aware configuration patterns. The repository already includes environment variables in `.env.example`, Docker compose files under `docker/`, and workflow files under `.github/workflows/`.

## Current enterprise evolution goal

PesaGuard is evolving toward a secure, observable, and testable fintech platform using the existing Flask and queue-oriented backend rather than replacing it with a new framework.
