# Security policy

## Supported versions

| Version | Security fixes |
| --- | --- |
| Latest published preview | Current maintenance target |
| Older previews | Update to the latest preview |
| `main` development branch | Under development; not a supported installed release |

BloonsPlus is in preview. Maintenance is best effort; there is no guaranteed response time or bug bounty. Review the [release notes](https://github.com/Klaasawastaken/BloonsPlus/releases) for known limitations.

## Report privately

Use [GitHub's private vulnerability form](https://github.com/Klaasawastaken/BloonsPlus/security/advisories/new). If the form is unavailable, privately contact **klaasa** or project staff through the [official Discord](https://discord.gg/qxUGXqrXsY) and ask for a private reporting channel before sending sensitive details.

Do not publish exploit details in a public issue, PR or Discord channel. Routine route defeats, setup failures and display bugs belong in the normal bug form unless they involve a security risk.

Include:

- Affected release, component and relevant Windows/runtime versions.
- A description of the impact and the access or conditions required.
- Minimal reproduction steps or a safe proof of concept using dummy data.
- Whether the issue is known to be publicly disclosed.

Do not send real passwords, session tokens, private keys, account saves or complete VM images. Redact identifying information from logs and screenshots. A maintainer may request a smaller sanitized example during triage.

## Coordinated handling

Maintainers will assess the report, ask for missing details, and discuss a fix or mitigation with the reporter. Please coordinate public disclosure so users can update first. Reporter credit is offered with their consent; private reports do not imply permission to publish a person's identity.

Test only systems and accounts you own or are authorized to assess. Keep testing minimal and non-destructive. Do not change game/save files, access other users' data or interrupt an active replay to demonstrate a vulnerability.
