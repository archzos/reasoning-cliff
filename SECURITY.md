# Security Policy

## Supported versions

This repository is pre-1.0. Security fixes target the latest `main` branch.

## Reporting a vulnerability

Please do not file public issues for vulnerabilities.

Report privately to: `anuj@archzos.com`

Include:
- Affected component(s)
- Reproduction steps / proof of concept
- Impact assessment
- Suggested remediation (if available)

You can expect:
- Initial acknowledgement within 72 hours
- Triage and severity assessment
- Coordinated disclosure after a fix is available

## Scope

In scope:
- Result-store data leakage
- Unsafe defaults in runner/adapters
- Misleading failure classification that can materially affect conclusions
- Credential handling and accidental secret exposure

Out of scope:
- Vulnerabilities only present in forks or modified deployments
- Issues requiring non-default, explicitly insecure configuration
