# Security Policy

PesaGuard handles sensitive financial transaction data (M-Pesa callbacks, reconciliation records, and account details) on behalf of SACCOs, e-commerce operators, and fintechs. We take the security of this data seriously.

## Supported Versions

| Version | Supported |
|---|---|
| Latest (main branch) | ✅ |
| Pre-MVP / archived branches | ❌ |

As PesaGuard is in active MVP/pilot-stage development, only the current production deployment receives security patches.

## Reporting a Vulnerability

**Please do not open a public GitHub issue for security vulnerabilities.**

If you discover a security issue — including but not limited to:
- Webhook signature bypass or spoofing
- Unauthorized access to transaction or reconciliation data
- Injection vulnerabilities (SQL, command, etc.)
- Authentication or authorization flaws
- Exposure of API keys, credentials, or secrets

please report it privately by emailing **[your-security-contact-email]** or opening a [private security advisory on GitHub](https://github.com/Victor-Kipruto-Rop/pesaguard/security/advisories/new).

Include:
- A description of the vulnerability and its potential impact
- Steps to reproduce (proof-of-concept if possible)
- Any relevant logs, payloads, or screenshots

**Response time:** We aim to acknowledge reports within 48 hours and provide a remediation timeline within 5 business days.

## Scope

In scope:
- The PesaGuard application (API, webhook receiver, dashboard)
- Infrastructure configuration under our control (Render deployment, database access controls)

Out of scope:
- Safaricom Daraja API itself
- Third-party services PesaGuard integrates with but does not control
- Denial-of-service attacks against shared free-tier infrastructure

## Security Practices

PesaGuard follows these practices to protect transaction data:

- **Webhook verification** — all M-Pesa Daraja callbacks are validated for authenticity and processed idempotently to prevent replay or duplicate-processing attacks.
- **Secrets management** — API keys, Daraja credentials, and database credentials are stored as environment variables, never committed to source control.
- **Least privilege** — database and service accounts are scoped to the minimum access required.
- **Encryption in transit** — all API and webhook traffic is served over HTTPS/TLS.
- **Input validation** — all incoming payloads (webhooks, API requests) are validated and sanitized before processing.
- **Dependency hygiene** — dependencies are kept up to date; known-vulnerable packages are patched promptly.

*(Update this list to reflect what's actually implemented — e.g. specific auth method, whether data is encrypted at rest, rate limiting, audit logging, etc.)*

## Disclosure Policy

We ask that reporters give us a reasonable window to investigate and patch a vulnerability before any public disclosure. We're happy to credit researchers who report responsibly, with permission.

## Contact

Victor Kipruto Rop — [GitHub](https://github.com/Victor-Kipruto-Rop)
