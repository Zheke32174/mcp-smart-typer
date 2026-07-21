# Security Policy

## Supported status

MCP Smart Typer has no approved public package release at this time. The active TypeScript package is a mock-backed development server, and the Windows native helpers remain experimental.

Security fixes are prepared on draft branches and are not considered deployed until they have been reviewed, validated against the exact head, and deliberately released.

## Reporting a vulnerability

Please use GitHub's private vulnerability-reporting or Security Advisory interface for this repository when available.

Do not include credentials, tokens, private hostnames, private network addresses, personal data, screenshots containing sensitive content, or exploitable proof-of-concept payloads in a public issue.

Include:

- the affected commit, file, package, or candidate artifact;
- the expected and observed authority boundary;
- reproduction steps that avoid real credentials and unrelated systems;
- impact and prerequisites;
- any proposed containment or regression test.

Ordinary bugs without sensitive security details may be filed in GitHub Issues.

## Current high-risk boundaries

Reports are especially useful for:

- MCP tool registration or authorization that permits self-granted authority;
- real keyboard, mouse, browser, OCR, or UIA actions escaping dry-run or mock mode;
- logging or returning sensitive field values;
- package metadata or release workflows claiming false ownership or provenance;
- candidate artifacts containing source, tests, credentials, local paths, or files outside the declared package boundary;
- unsigned or mutable release identity;
- CI workflows that mask failures or publish from unreviewed refs.

## Disclosure

Please allow time for a draft fix and exact-head validation before public disclosure. No response-time or release-time guarantee is currently offered.
