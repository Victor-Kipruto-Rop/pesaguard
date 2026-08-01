# GitHub Protection Setup (Staging + Production)

This document captures the repository settings that cannot be fully enforced from code and must be set in GitHub UI.

## 1) Environments and required reviewers

Create/update environments:
- `staging`
- `production`

For each environment:
- Add required reviewers (at least 1 approver).
- Restrict deployment branches:
  - `staging` environment: allow only `staging` branch.
  - `production` environment: allow only `main` branch.
- Scope secrets to the environment instead of repository where possible.

Required environment secrets:

Staging:
- `STAGING_HOST`
- `STAGING_USER`
- `STAGING_SSH_KEY`
- `GHCR_DEPLOY_TOKEN`
- Optional: `STAGING_PATH`

Production:
- `PROD_HOST`
- `PROD_USER`
- `PROD_SSH_KEY`
- `GHCR_DEPLOY_TOKEN`
- Optional: `PROD_PATH`

## 2) Branch protection rules

Add rules for both branches: `main` and `staging`.

Enable:
- Require a pull request before merging.
- Require approvals (recommended: 1+ for staging, 2+ for main).
- Dismiss stale pull request approvals when new commits are pushed.
- Require status checks to pass before merging.
- Require branches to be up to date before merging.
- Restrict who can push to matching branches.
- Include administrators.

Required status checks to select:
- `Backend Tests`
- `Migration Dry Run`
- `Backup Restore Verify`
- `Image Build`
- `Dependency Review`
- `Secret Scan`
- `Python Security`
- `Frontend Security`

## 3) Secret scanning and dependency policies

In GitHub Security settings:
- Enable secret scanning.
- Enable push protection for secret scanning.
- Enable Dependabot alerts.
- Enable Dependabot security updates.
- Enable dependency graph.

## 4) Deployment flow

Staging deploy workflow:
- `.github/workflows/deploy-staging.yml`

Production deploy workflow:
- `.github/workflows/deploy-production.yml`

Production deploy is manually triggered and includes a required environment approval gate before deployment.
