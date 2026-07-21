# Public Release-Readiness Checkpoint

Repository: `Zheke32174/mcp-smart-typer`  
Draft branch: `workflow/verified-publication-v1`  
Draft pull request: `#4`  
Default branch changed: no  
Registry publication authority: none

## Last reviewed heads

- Release-boundary checkpoint: `be000476841d07daf8054ffbd4e1f0e494ab450a`
- Broad normalization head: `74158dc93db9c421102b6e036e676448732dc251`
- Exact Python boundary repair: `67915a9cc0e195e04afe451fb761204fd60d4cca`
- Successful broad normalization run: `29792815675`
- Successful Python boundary repair run: `29800085160`

## Completed scope

- Replaced false upstream npm provenance with repository-owned package metadata.
- Removed ordinary-main-push publication and kept publication authority absent.
- Made Python and Node failures visible instead of converting them to success.
- Bound third-party Actions to full commit identities and removed persisted checkout credentials from read-only CI.
- Built tag-bound npm and Windows executable candidates without publishing them.
- Added exact candidate checksums and a source-bound build receipt.
- Restricted the npm candidate tarball to declared runtime files.
- Replaced the public npm entry point's self-granting security-control surface with the four-tool mock development server.
- Corrected public installation, package-name, capability, performance, support, and security claims.
- Added a repository security-reporting boundary.
- Repaired the serialized tail in `standalone_production_demo.py` and declared the pandas dependency.
- Removed illegal `U+001E` control bytes from `ui_automation.py`.
- Made TensorFlow an optional accelerator; the documented rule-based classifier remains importable when TensorFlow is absent.
- Excluded generated protobuf output from formatter and mypy authority while retaining regeneration and package compilation in CI.
- Normalized owned Python and TypeScript source and aligned the mock server's self-reported version with package version `2.0.0`.
- Replaced EOL Node 18/20 validation with supported Node 22/24 LTS validation and npm `10.9.3`.
- Added durable Node lint diagnostics to failed exact-head runs.
- Removed both temporary write-capable repair workflows after their successful commits.

## Validation receipts

Broad repair run `29792815675` passed exact checkout, serialized-tail decoding, parsable-Python normalization, locked Node installation, TypeScript formatting and safe autofixes, mock-version alignment, compilation, patch hygiene, self-removal, and branch publication.

Python boundary repair run `29800085160` passed exact checkout, UI control-byte repair, optional-TensorFlow conversion, targeted Black/isort normalization, exact-file compilation, patch hygiene, self-removal, and branch publication.

The bot-authored repair head produced `action_required` placeholders with zero jobs. This ledger update intentionally supplies a normal exact-head trigger. Repair success is not a release approval.

## External practices applied

- npm package allowlisting through `package.json#files`; npm otherwise defaults to broad package inclusion.
- Repository-exact npm metadata and a public scoped-package access declaration.
- Full-SHA Action references and least-privilege read-only validation.
- Supported LTS runtimes only; Node.js marks 18 and 20 EOL and identifies 22 and 24 as LTS as of July 2026.
- Mock-by-default execution until an authenticated native transport exists.
- Candidate-only builds until a separately reviewed trusted-publishing workflow and registry configuration exist.

Primary references:

- https://docs.npmjs.com/files/package.json/
- https://docs.npmjs.com/trusted-publishers/
- https://docs.github.com/en/actions/reference/security/secure-use
- https://nodejs.org/en/about/previous-releases
- https://nodejs.org/en/about/eol

## Open blockers

1. Node lint, typecheck, build, and tests require a green exact-head receipt on Node 22 and 24.
2. Python compile, formatting, import ordering, mypy, tests, and executable build require a green exact-head receipt.
3. The native Windows transport is not authenticated or integrated with the npm entry point.
4. No disposable Windows interaction receipt proves safe live UI automation.
5. No npm trusted publisher is configured, and no publication workflow is approved.
6. No package-registry ownership or availability check has been recorded for `@mcp-smart-typer/server`.
7. Administrative branch/ruleset and private-vulnerability-reporting settings are not source-verifiable.

## Deferred work

- Evaluate OIDC trusted publishing only after package ownership and candidate behavior are green.
- Require Node 22.14+ and npm 11.5.1+ if npm trusted publishing is adopted.
- Decide whether the native-helper executable should be a separate GitHub Release asset rather than an npm package payload.
- Add dependency review or CodeQL after the core build is stable enough to produce meaningful signal.

## Reconsideration triggers

Reprocess this repository only when the draft head, CI/diagnostic/advisory state, package ownership, native transport, public claims, release authority, or explicit steward instruction changes.

## Next action

Inspect CI triggered by this ledger update. Use the uploaded Node lint artifact and Python diagnostics to repair only exact remaining failures on this same draft branch. Keep the repository on `HOLD` until both language surfaces are green and the package remains mock-only by default.
