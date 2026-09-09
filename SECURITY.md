# Security Policy

## Supported Versions

Plugin Autopilot is maintained on the `main` branch. Only the latest release on `main` receives security updates.

| Version | Supported |
| --- | --- |
| Latest on `main` | :white_check_mark: |
| < Latest release | :x: |

---

## Reporting a Suspected Vulnerability

We take the security of Plugin Autopilot and downstream developer environments seriously.

> [!IMPORTANT]
> **Do not disclose suspected security vulnerabilities or sensitive evidence in public GitHub Issues, Pull Requests, or discussions.**
> Public issue trackers must remain free of credentials, private source code, live tokens, and weaponized exploit material.

### Primary Reporting Route

Please report suspected vulnerabilities using **GitHub Private Vulnerability Reporting**:

1. Navigate to the repository's [Security Advisories](https://github.com/imMamdouhaboammar/chatgpt-codex-plugin-autopilot/security/advisories) tab.
2. Click **Report a vulnerability** (or open [`/security/advisories/new`](https://github.com/imMamdouhaboammar/chatgpt-codex-plugin-autopilot/security/advisories/new)).
3. Fill out the advisory form with a clear summary, impact analysis, and reproduction steps.

This routes the advisory directly to repository maintainers in a private channel before any public disclosure.

### Fail-Closed Fallback Route

If GitHub's native private vulnerability reporting interface is unavailable, disabled, or inaccessible to your account:

- **Do not post sensitive reproduction evidence or exploit details publicly.**
- Contact the maintainer privately through their verified GitHub profile contact details.
- Alternatively, open an issue requesting the maintainer open a private security advisory draft, stating only that you have a private security inquiry and omitting any sensitive reproduction details, credentials, or exploit code.

---

## What Belongs in Private Security Disclosure vs. Public Issues

| Category | Channel | Examples |
| --- | --- | --- |
| **Private Security Disclosure** | GitHub Security Advisory | • Path traversal or arbitrary file read/write bypassing packaging or validation filters.<br>• Unintended shell command injection or execution escapes in helper scripts.<br>• Secret leakage, token harvesting, or credential exposure in generated packs.<br>• Integrity tampering, hash bypass, or packaging verification circumvention.<br>• Trust-boundary escapes between host workspace and skill execution boundaries. |
| **Public Issues** | GitHub Issues | • Validation schema false positives on valid plugin manifests.<br>• General compatibility issues with newer Python or OS versions.<br>• Documentation errors, typos, or clarification requests.<br>• Feature enhancements and workflow improvements. |

---

## What to Include in a Report

To help us investigate effectively, please include:
- A descriptive summary of the behavior and its security impact.
- Exact environment details (Python version, operating system, Plugin version/commit).
- Minimal, sanitized reproduction steps or test fixtures.
- **Never include**: live credentials, production API keys, proprietary repository code, or unnecessarily weaponized exploit payloads.

---

## Trust Boundaries & Security Model

- **Public Tracker Boundary**: GitHub Issues and Pull Requests are public. Reporters are unauthorized to post sensitive credentials or exploits there.
- **Private Disclosure Boundary**: Suspected vulnerabilities and sensitive reproduction evidence must cross strictly into a maintainer-controlled private channel before details are shared.
- **Repository and Tool Boundary**: Plugin Autopilot provides instructions, skills, and Python validation/packaging scripts for host-provided workspace, shell, and release operations. While Plugin Autopilot operates no publisher-hosted backend, local execution scripts and mutation boundary guidance must maintain strict host containment, follow fail-closed validation, and never silently execute unverified operations.
- **Affected Roles**: Security researchers, repository maintainers, and downstream plugin authors/users who rely on packaging, validation, and execution guardrails.

---

## Response & Disclosure Process

Maintainers will review private reports, acknowledge receipt, investigate the root cause, develop and verify fixes privately, and coordinate public disclosure alongside a patched release. No commercial SLAs or bug-bounty payouts are offered.
