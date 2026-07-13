# PesaGuard Readiness Roadmap — Advanced and Production-Ready

## Overview
This roadmap upgrades the existing readiness work into a robust operating model for a premium pilot and future commercial rollout. The focus is on operational resilience, trust, governance, and customer confidence.

## Tiered rollout model
### Starter / Pilot
- Single-tenant or small pilot deployment
- Manual operational monitoring acceptable
- Backup and restore verified at least once
- Basic retention policy enforced

### Moderate
- Multi-tenant support with stronger isolation and auditability
- Automated backup and retention enforcement in production
- Clear incident response workflow and customer communication
- Formal support and SLA expectations

### Premium
- Business-grade reliability and compliance posture
- Dedicated backup validation, restore drills, and incident rehearsal
- Stronger legal/commercial readiness and tenant lifecycle controls
- Clear product scope, localization, and data residency posture

## Core workstreams
### 1. Technical hardening
- Finish package/import compatibility for test and runtime execution
- Ensure the retention job is deployed and verified in the target environment
- Add automated backup orchestration and scheduled restore validation

### 2. Operational resilience
- Daily backup automation
- Offsite backup storage
- Restore drill in a non-production environment
- Runbook for incident response, escalation, and customer communication
- Monitoring and alerting for backup, retention, and service health

### 3. Governance and trust
- Terms of Service
- Privacy Policy
- DPA
- ODPC review and compliance assessment
- Liability/E&O review
- Pilot agreement and support plan

### 4. Product maturity
- Clear scope boundary for M-Pesa/Daraja only versus future expansion
- Localization for English and Kiswahili
- Data residency documentation and deployment configuration
- Customer-facing onboarding and offboarding materials

## Recommended next actions
1. Formalize the premium operating posture in documentation.
2. Implement and verify scheduled backup and retention jobs.
3. Prepare the legal/commercial package for pilot customers.
4. Publish a simple status page and support channel.
5. Rehearse a restore and incident drill before wider rollout.
