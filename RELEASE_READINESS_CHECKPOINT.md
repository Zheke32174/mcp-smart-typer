# Public Release-Readiness Checkpoint

Repository: `Zheke32174/mcp-smart-typer`  
Draft branch: `workflow/verified-publication-v1`  
Draft pull request: `#4`  
Default branch changed: no  
Registry publication authority: none

## Last reviewed heads and receipts

- Last strict npm validation head: `1fd39c26e85b3828407779d1d5b3170451802890`
- Coherent package-policy implementation head: `d79845cac1ac69a769e62ce461e379638ac5da67`
- Mock-only npm boundary repair: `ed089f1e04bae3c861f92151e6ecbe89c49b1ee4`
- Strict npm CI run: `29835935555`
- npm lock-consistency run: `29835935450`
- Source-normalization diagnostic run: `29835935590`
- Successful broad normalization run: `29792815675`
- Successful Python boundary repair run: `29800085160`
- Successful runtime-validation repair run: `29812734653`

## Completed scope

- Replaced false upstream npm provenance with repository-owned package metadata.
- Removed ordinary-main-push publication and kept publication authority absent.
- Made failures visible instead of converting them to success.
- Bound third-party Actions to full commit identities and removed persisted checkout credentials from read-only workflows.
- Added exact candidate checksums and source-bound build receipts.
- Restricted the npm candidate tarball to declared runtime files.
- Replaced the public npm entry point's self-granting security-control surface with a mock-backed development server.
- Corrected public installation, package-name, capability, performance, support, and security claims.
- Repaired malformed Python source, illegal control bytes, formatter drift, missing pandas declaration, and import-time optional-TensorFlow failure.
- Corrected the ESLint preset and invalid `@typescript-eslint/prefer-const` rule reference.
- Replaced EOL Node 18/20 validation with Node 22/24 LTS and npm `10.9.3`.
- Added `.gitattributes` so text release inputs remain LF-normalized on Linux and Windows.
- Split the npm release surface from the experimental Windows native helper.
- Reduced npm runtime dependencies to the MCP SDK and Zod.
- Added `tsconfig.release.json` covering only the bounded mock package.
- Added a mock-only release contract test and actual `npm pack` boundary inspection.
- Added the package-local MIT license required by the tarball contract.
- Replaced the stale unified tag workflow with a tag-only npm candidate workflow that excludes the native helper, rejects tags not reachable from `main`, creates checksums and a source-bound receipt, and has no publication authority.
- Added practical local candidate installation, update, rollback, and removal instructions without implying registry availability.
- Added a durable release-policy log artifact.
- Removed the native-helper matrix from strict npm CI.
- Moved native-helper compilation, formatting, typing, and focused test evidence into a separate path-scoped, read-only, explicitly nonblocking workflow.
- Decoupled npm version preparation from the experimental Python helper; npm release preparation now changes only the monorepo and mock package identities and records that the native-helper version was untouched.
- Updated the canonical policy validator to enforce the split workflows and independent release identities.

## Validation receipts

At exact head `1fd39c26e85b3828407779d1d5b3170451802890`:

- canonical release policy passed and uploaded a durable policy receipt;
- npm lock consistency passed;
- source-normalization diagnostics passed;
- Node 22 locked install passed;
- Node 22 bounded lint, typecheck, build, mock-only contract, and tarball inspection passed;
- Node 24 locked install passed;
- Node 24 bounded lint, typecheck, build, mock-only contract, and tarball inspection passed;
- the package-local README, LICENSE, manifest, and built entry point were present in the inspected npm archive;
- source, tests, scripts, and `node_modules` did not escape the npm archive.

The strict mock-package release gate is green. Native-helper findings remain separate diagnostic evidence and are not npm release failures.

## External practices applied

- npm package allowlisting through `package.json#files`; npm otherwise defaults to broad inclusion.
- Package-local README and LICENSE inclusion verified against the actual `npm pack` file list.
- Full-SHA Action references and least-privilege read-only validation.
- Node 22 and 24 LTS release testing; Node 20 is EOL as of March 24, 2026.
- Separate release gates and identities for a distributable npm package and an experimental platform-specific subsystem.
- Candidate-only builds until package ownership and a separately reviewed trusted-publishing workflow exist.
- Trusted publishing remains deferred; current npm guidance requires Node `22.14.0+`, npm `11.5.1+`, and an explicitly configured OIDC publisher.

Primary references:

- https://docs.npmjs.com/files/package.json/
- https://docs.npmjs.com/trusted-publishers/
- https://docs.github.com/en/actions/reference/security/secure-use
- https://nodejs.org/en/about/previous-releases

## Open blockers

1. Package-registry ownership and availability of `@mcp-smart-typer/server` remain unverified.
2. No npm trusted publisher is configured and no publication workflow is approved.
3. The native Windows helper remains experimental: mypy debt, test debt, unauthenticated transport, no disposable interaction receipt, and no approved standalone artifact policy.
4. Administrative branch/ruleset and private-vulnerability-reporting settings remain outside source-level verification.

## Deferred work

- Evaluate OIDC trusted publishing only after package ownership is confirmed.
- Require Node `22.14+` and npm `11.5.1+` if npm trusted publishing is adopted.
- Decide whether a repaired native-helper executable should become a separate GitHub Release asset.
- Add dependency review or CodeQL after the bounded package branch is integrated and produces stable signal.

## Reconsideration triggers

Reprocess this repository only when the draft head, strict npm CI state, package ownership, public claims, release authority, dependency advisory state, native-helper inputs, or explicit steward instruction changes.

## Next action

Skip further mock-package source reprocessing unless its head or evidence changes. The next substantive checkpoint is package-name ownership and publication-authority design. Continue native-helper hardening only in its separate experimental backlog and workflow.
