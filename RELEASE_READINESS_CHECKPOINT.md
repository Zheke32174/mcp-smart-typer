# Public Release-Readiness Checkpoint

Repository: `Zheke32174/mcp-smart-typer`  
Draft branch: `workflow/verified-publication-v1`  
Draft pull request: `#4`  
Default branch changed: no  
Registry publication authority: none

## Last reviewed head

- Head before this checkpoint: `3734652d608b3b0564a40d3f1a3e9e7371c3c888`
- Last CI run inspected: `29711519353`
- Python diagnostic run inspected: `29711519345`

## Completed scope

- Replaced false upstream npm provenance with repository-owned package metadata.
- Removed ordinary-main-push publication.
- Made Python and Node failures visible instead of converting them to success.
- Pinned third-party Actions to full commit identities.
- Built tag-bound npm and Windows executable candidates without publishing them.
- Added exact candidate checksums and a source-bound build receipt.
- Narrowed the npm tarball to declared runtime files.
- Replaced the public npm entry point's self-granting security-control surface with a mock-only development server.
- Corrected public installation, package-name, capability, performance, and security claims.
- Added a repository security-reporting boundary.
- Repaired one corrupted Python source file and declared the missing pandas dependency.
- Excluded generated protobuf output from formatter authority while retaining regeneration in CI.

## Validation receipts already available

At head `3734652d608b3b0564a40d3f1a3e9e7371c3c888`:

- release-policy validation passed;
- npm lock consistency passed;
- Python diagnostics and primary CI failed honestly;
- Python failures were traced to source formatting, one corrupted source tail, and an undeclared pandas dependency;
- Node CI reached ESLint and failed before typecheck/build/test.

These are defect receipts, not release approvals.

## External practices applied

- npm package allowlisting through `package.json#files`, rather than relying on the default all-files pack behavior.
- repository-exact npm metadata and a public scoped-package access declaration.
- full-SHA Action references and least-privilege read-only validation.
- candidate-only builds until a separately reviewed trusted-publishing workflow and registry configuration exist.

Primary references:

- npm `package.json` file-selection rules: https://docs.npmjs.com/files/package.json/
- npm trusted publishing: https://docs.npmjs.com/trusted-publishers/
- GitHub Actions secure-use reference: https://docs.github.com/en/actions/reference/security/secure-use

## Open blockers

1. Node lint, typecheck, build, and tests do not yet have a green exact-head receipt.
2. Python formatting, mypy, tests, and executable build require a fresh exact-head receipt after normalization.
3. The native Windows transport is not authenticated or integrated with the npm entry point.
4. No disposable Windows interaction receipt proves safe live UI automation.
5. No npm trusted publisher is configured, and no publication workflow is approved.
6. No package-registry ownership or availability check has been recorded for `@mcp-smart-typer/server`.
7. The default branch does not yet contain the release-readiness work.
8. Administrative branch/ruleset and private-vulnerability-reporting settings are not source-verifiable.

## Deferred work

- Evaluate OIDC trusted publishing only after the package name is owned and candidate behavior is green.
- Require Node 22.14+ and npm 11.5.1+ if trusted publishing is adopted.
- Decide whether the native-helper executable should be a separate GitHub Release asset rather than an npm package payload.
- Add dependency review or CodeQL after the core build is stable enough to produce meaningful signal.

## Reconsideration triggers

Reprocess this repository when any of the following changes:

- draft branch head;
- CI, diagnostic, dependency, or advisory status;
- package name or registry ownership;
- native transport design;
- public capability or performance claims;
- release workflow authority;
- explicit steward instruction.

## Next action

Inspect the first CI run after this checkpoint. Repair the exact remaining Node and Python failures on the same draft branch. Keep the repository on `HOLD` until both language surfaces are green and the package remains mock-only by default.
