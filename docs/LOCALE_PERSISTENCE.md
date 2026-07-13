## Locale persistence endpoint

Summary
- Added public endpoint `POST /tenant/current/locale` to persist the current runtime tenant's `preferred_locale`.
- Frontend sync: `frontend/lib/i18n.ts` now calls this endpoint when a user selects a locale; `frontend/app/settings/page.tsx` applies the locale on load/save.

Security review (brief)
- Threat: open POST endpoint may be used to toggle tenant UI locale repeatedly or create noise. The endpoint only updates a non-sensitive UX preference and writes to the pilot `tenant_settings.json` file.
- Recommendation: keep it public for pilot ease-of-use, but throttle or protect in production. Consider one of:
  - Require admin authentication for production tenants (via `X-Admin-Token`) and keep public endpoint as pilot-only.
  - Add a simple rate limit per remote IP for this endpoint.
  - Validate the incoming locale against an allow-list (`en`, `sw`) to avoid garbage writes.

Operational notes
- The endpoint uses the in-file `TenantSettingsStore` and writes to the file referenced by `TENANT_SETTINGS_FILE`.
- For production readiness:
  - Move settings to a durable store (DB) and apply transactional controls.
  - Add an audit log for changes to tenant preferences.

How to run the e2e test (dev)
1. Start the backend API (Flask) and set `TENANT_ID` to the target tenant.
2. Start the frontend: `cd frontend && npm run dev` (port 3000)
3. Install dev deps: `cd frontend && npm install` (install Playwright)
4. Run tests: `cd frontend && npx playwright test e2e/tests/locale.spec.ts`
