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
- Runtime-validation repair head: `62b27c1ddd68fe603354273ac6b7ecd0a8ac5582`
- Successful broad normalization run: `29792815675`
- Successful Python boundary repair run: `29800085160`
- Successful runtime-validation repair run: `29812734653`

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
- Made TensorFlow an optional accelerator and removed the import-time annotation dereference when TensorFlow is absent.
- Excluded generated protobuf output from formatter and mypy authority while retaining regeneration and package compilation in CI.
- Normalized every parsable owned Python runtime and test file and aligned the mock server's self-reported version with package version `2.0.0`.
- Corrected the ESLint preset from the nonexistent `@typescript-eslint/recommended` shareable-config name to `plugin:@typescript-eslint/recommended`.
- Replaced EOL Node 18/20 validation with supported Node 22/24 LTS validation and npm `10.9.3`.
- Aligned the canonical release-policy validator with the supported Node/npm identities and maintained-runtime matrix.
- Updated the lock-consistency workflow to Node 22, npm `10.9.3`, read-only checkout, and the committed lockfile.
- Regenerated `package-lock.json` from the exact committed package metadata with lifecycle scripts, audit, and funding calls disabled.
- Added durable Node lint diagnostics to failed exact-head runs.
- Removed all temporary write-capable repair workflows after successful commits.

## Validation receipts

Broad repair run `29792815675` passed exact checkout, serialized-tail decoding, parsable-Python normalization, locked Node installation, TypeScript formatting and safe autofixes, mock-version alignment, compilation, patch hygiene, self-removal, and branch publication.

Python boundary repair run `29800085160` passed exact checkout, UI control-byte repair, optional-TensorFlow conversion, targeted Black/isort normalization, exact-file compilation, patch hygiene, self-removal, and branch publication.

Runtime-validation repair run `29812734653` passed exact branch checkout, idempotent optional-TensorFlow annotation repair, per-file Python compilation and normalization, npm `10.9.3` lock synchronization, locked dependency installation, canonical release-policy validation, patch hygiene, remaining-lint capture, self-removal, and branch publication.

The bot-authored repair head `62b27c1ddd68fe603354273ac6b7ecd0a8ac5582` produced `action_required` placeholders with zero jobs. This ledger commit intentionally supplies a normal exact-head trigger. The repair receipts prove source mutation and deterministic validation boundaries, not release approval.

## External practices applied

- npm package allowlisting through `package.json#files`; npm otherwise defaults to broad package inclusion.
- Repository-exact npm metadata and a public scoped-package access declaration.
- Full-SHA Action references and least-privilege read-only validation.
- Supported LTS runtimes only; Node.js identifies 22 and 24 as LTS and marks Node 20 EOL as of March 24, 2026.
- Correct TypeScript ESLint legacy configuration through `plugin:@typescript-eslint/recommended` rather than an unresolved shareable-config package name.
- Mock-by-default execution until an authenticated native transport exists.
- Candidate-only builds until a separately reviewed trusted-publishing workflow and registry configuration exist.
- npm trusted publishing remains deferred; current npm guidance requires Node `22.14.0+` and npm `11.5.1+`, plus an explicitly configured OIDC publisher.

Primary references:

- https://docs.npmjs.com/files/package.json/
- https://docs.npmjs.com/trusted-publishers/
- https://docs.github.com/en/actions/reference/security/secure-use
- https://nodejs.org/en/about/previous-releases
- https://typescript-eslint.io/getting-started/legacy-eslint-setup/

## Open blockers

1. Node lint, typecheck, build, and tests require a green exact-head receipt on Node 22 and 24. The configuration-loader failure is resolved; any remaining lint findings are source debt.
2. Python compile, formatting, import ordering, mypy, tests, and executable build require a green exact-head receipt. Import-time optional-TensorFlow failure and formatter drift are resolved; remaining mypy or behavior failures must be evaluated on their merits.
3. The native Windows transport is not authenticated or integrated with the npm entry point.
4. No disposable Windows interaction receipt proves safe live UI automation.
5. No npm trusted publisher is configured, and no publication workflow is approved.
6. No package-registry ownership or availability check has been recorded for `@mcp-smart-typer/server`.
7. Administrative branch/ruleset and private-vulnerability-reporting settings are not source-verifiable.

## Deferred work

- Evaluate OIDC trusted publishing only after package ownership and candidate behavior are green.
- Require Node `22.14+` and npm `11.5.1+` if npm trusted publishing is adopted.
- Decide whether the native-helper executable should be a separate GitHub Release asset rather than an npm package payload.
- Add dependency review or CodeQL after the core build is stable enough to produce meaningful signal.

## Reconsideration triggers

Reprocess this repository only when the draft head, CI/diagnostic/advisory state, package ownership, native transport, public claims, release authority, or explicit steward instruction changes.

## Next action

Inspect CI triggered by this ledger update. Repair only the exact remaining Node source lint/type/build/test failures and Python mypy/test failures on this same draft branch. Keep the repository on `HOLD` until both language surfaces are green and the package remains mock-only by default.
