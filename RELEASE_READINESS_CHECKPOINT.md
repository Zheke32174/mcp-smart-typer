# Public Release-Readiness Checkpoint

Repository: `Zheke32174/mcp-smart-typer`  
Draft branch: `workflow/verified-publication-v1`  
Draft pull request: `#4`  
Default branch changed: no  
Registry publication authority: none

## Last reviewed head

- Head before this checkpoint: `3734652d608b3b0564a40d3f1a3e9e7371c3c888`
- Coherent release-boundary checkpoint: `be000476841d07daf8054ffbd4e1f0e494ab450a`
- Repaired and normalized source head: `74158dc93db9c421102b6e036e676448732dc251`
- Successful one-shot repair run: `29792815675`

## Completed scope

- Replaced false upstream npm provenance with repository-owned package metadata.
- Removed ordinary-main-push publication.
- Made Python and Node failures visible instead of converting them to success.
- Kept third-party Actions bound to full commit identities.
- Built tag-bound npm and Windows executable candidates without publishing them.
- Added exact candidate checksums and a source-bound build receipt.
- Restricted the npm candidate tarball to declared runtime files.
- Replaced the public npm entry point's self-granting security-control surface with the four-tool mock development server.
- Corrected public installation, package-name, capability, performance, support, and security claims.
- Added a repository security-reporting boundary.
- Repaired the serialized tail in `standalone_production_demo.py`.
- Declared the missing pandas dependency in both authoritative and compatibility dependency files.
- Excluded generated protobuf output from formatter authority while retaining regeneration in CI.
- Normalized every parsable owned Python file and applied Prettier plus safe ESLint autofixes to the TypeScript surface.
- Aligned the mock server's self-reported version with package version `2.0.0`.
- Removed the temporary write-capable normalization workflow after its successful commit.

## Validation receipts

At checkpoint head `be000476841d07daf8054ffbd4e1f0e494ab450a`:

- release-policy validation passed;
- npm lock consistency passed;
- Python CI failed honestly at the expected pre-normalization formatting gate;
- Node CI failed honestly at the expected pre-normalization lint gate.

Repair run `29792815675` then passed every stage:

- exact branch checkout;
- serialized Python-tail decoding;
- parsable-Python normalization;
- locked Node dependency installation;
- TypeScript formatting and safe autofixes;
- mock-server version alignment;
- repaired-source compilation and patch-hygiene checks;
- self-removal and publication of one normalization commit.

A fresh read-only CI receipt is required for the post-repair head. Repair success is not a release approval.

## External practices applied

- npm package allowlisting through `package.json#files`, rather than relying on the default all-files pack behavior.
- repository-exact npm metadata and a public scoped-package access declaration.
- full-SHA Action references and least-privilege read-only validation.
- mock-by-default execution until an authenticated native transport exists.
- candidate-only builds until a separately reviewed trusted-publishing workflow and registry configuration exist.

Primary references:

- npm `package.json` file-selection rules: https://docs.npmjs.com/files/package.json/
- npm trusted publishing: https://docs.npmjs.com/trusted-publishers/
- GitHub Actions secure-use reference: https://docs.github.com/en/actions/reference/security/secure-use

## Open blockers

1. Node lint, typecheck, build, and tests require a green exact post-repair receipt.
2. Python formatting, import ordering, mypy, tests, and executable build require a green exact post-repair receipt.
3. Any malformed Python files skipped by salvage formatting must be named and repaired from the next diagnostic receipt.
4. The native Windows transport is not authenticated or integrated with the npm entry point.
5. No disposable Windows interaction receipt proves safe live UI automation.
6. No npm trusted publisher is configured, and no publication workflow is approved.
7. No package-registry ownership or availability check has been recorded for `@mcp-smart-typer/server`.
8. Administrative branch/ruleset and private-vulnerability-reporting settings are not source-verifiable.

## Deferred work

- Evaluate OIDC trusted publishing only after package ownership and candidate behavior are green.
- Require Node 22.14+ and npm 11.5.1+ if npm trusted publishing is adopted.
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

Inspect CI triggered by this ledger update. Repair only the exact remaining post-normalization failures on the same draft branch. Keep the repository on `HOLD` until both language surfaces are green and the package remains mock-only by default.
