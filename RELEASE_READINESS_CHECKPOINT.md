# Public Release-Readiness Checkpoint

Repository: `Zheke32174/mcp-smart-typer`  
Draft branch: `workflow/verified-publication-v1`  
Draft pull request: `#4`  
Default branch changed: no  
Registry publication authority: none

## Last reviewed heads and receipts

- Prior exact-head diagnostics: `c449266a47b1b5650c32d5994b0b348e2f8eabbd`
- Mock-only npm boundary repair: `ed089f1e04bae3c861f92151e6ecbe89c49b1ee4`
- Last reviewed ledger head: `b266975372f726c605f105d4e17740a6b32fe601`
- Exact-head CI run: `29828726516`
- npm lock-consistency run: `29828726558`
- Successful broad normalization run: `29792815675`
- Successful Python boundary repair run: `29800085160`
- Successful runtime-validation repair run: `29812734653`

## Completed scope

- Replaced false upstream npm provenance with repository-owned package metadata.
- Removed ordinary-main-push publication and kept publication authority absent.
- Made Python and Node failures visible instead of converting them to success.
- Bound third-party Actions to full commit identities and removed persisted checkout credentials from read-only CI.
- Added exact candidate checksums and a source-bound build receipt.
- Restricted the npm candidate tarball to declared runtime files.
- Replaced the public npm entry point's self-granting security-control surface with a mock-backed development server.
- Corrected public installation, package-name, capability, performance, support, and security claims.
- Repaired malformed Python source, illegal control bytes, formatter drift, missing pandas declaration, and import-time optional-TensorFlow failure.
- Corrected the ESLint preset and invalid `@typescript-eslint/prefer-const` rule reference.
- Replaced EOL Node 18/20 validation with Node 22/24 LTS and npm `10.9.3`.
- Added `.gitattributes` so text release inputs remain LF-normalized on Linux and Windows.
- Split the npm release surface from the experimental Windows native helper.
- Reduced npm runtime dependencies to the MCP SDK and Zod; native OCR, browser, gRPC, TensorFlow, and image dependencies no longer enter the mock package.
- Added `tsconfig.release.json` covering only `index.ts`, `simple-server.ts`, schemas, and the three mock/runtime utilities.
- Added a mock-only release contract test and an `npm pack --dry-run --json` archive-boundary check.
- Moved strict Node release validation to Linux Node 22/24.
- Retained Windows Python 3.10/3.11/3.12 checks as nonblocking experimental diagnostics with uploaded Black, mypy, and pytest evidence.
- Removed the native executable build from the npm release gate.
- Added the package-local MIT license required by the declared tarball contract.
- Replaced the stale unified tag workflow with a tag-only npm candidate workflow that excludes the native helper, rejects tags not reachable from `main`, creates checksums and a source-bound receipt, and has no publication authority.
- Added practical local candidate installation, update, rollback, and removal instructions without implying registry availability.
- Updated the canonical policy validator to enforce the split architecture rather than requiring the experimental native subsystem to pass or ship with the npm package.

## Validation receipts

At head `b266975372f726c605f105d4e17740a6b32fe601`:

- npm lock consistency passed;
- source-normalization diagnostics passed;
- bounded npm source lint passed on Node 22 and 24;
- bounded npm source typecheck passed on Node 22 and 24;
- bounded npm build passed on Node 22 and 24;
- the mock-only release contract passed on Node 22 and 24;
- native helper source compiled and its nonblocking diagnostics were preserved on Python 3.10, 3.11, and 3.12;
- npm tarball inspection failed only because the package directory lacked its declared `LICENSE` file;
- canonical policy validation failed because it still required the retired unified native release model.

These receipts narrow the npm implementation debt to packaging and policy consistency. They are not registry or publication approval.

## External practices applied

- npm package allowlisting through `package.json#files`; npm otherwise defaults to broad inclusion.
- Package-local README and LICENSE inclusion verified against the actual `npm pack` file list.
- Full-SHA Action references and least-privilege read-only validation.
- Node 22 and 24 LTS release testing; Node 20 is EOL as of March 24, 2026.
- Separate release gates for a distributable package and an experimental platform-specific subsystem.
- Candidate-only builds until package ownership and a separately reviewed trusted-publishing workflow exist.
- Trusted publishing remains deferred; current npm guidance requires Node `22.14.0+`, npm `11.5.1+`, and an explicitly configured OIDC publisher.

Primary references:

- https://docs.npmjs.com/files/package.json/
- https://docs.npmjs.com/trusted-publishers/
- https://docs.github.com/en/actions/reference/security/secure-use
- https://nodejs.org/en/about/previous-releases

## Open blockers

1. The new package-license, policy, and tag-candidate boundary requires one green non-bot exact-head CI receipt.
2. Package-registry ownership and availability of `@mcp-smart-typer/server` remain unverified.
3. No npm trusted publisher is configured and no publication workflow is approved.
4. The native Windows helper remains experimental: mypy debt, test debt, unauthenticated transport, no disposable interaction receipt, and no approved standalone artifact policy.
5. Administrative branch/ruleset and private-vulnerability-reporting settings remain outside source-level verification.

## Deferred work

- Evaluate OIDC trusted publishing only after package ownership and candidate behavior are green.
- Require Node `22.14+` and npm `11.5.1+` if npm trusted publishing is adopted.
- Decide whether a repaired native-helper executable should become a separate GitHub Release asset.
- Add dependency review or CodeQL after the bounded package build is stable enough to produce useful signal.

## Reconsideration triggers

Reprocess this repository only when the draft head, exact-head CI or diagnostic state, package ownership, native transport, public claims, release authority, dependency advisory state, or explicit steward instruction changes.

## Next action

Inspect CI triggered by the coherent package-license, policy, candidate-workflow, README, and ledger commit. If Node 22/24, policy, lock, contract, and tarball checks pass, retain `HOLD` only for registry ownership and publication authority. Treat native Python findings as a separate experimental-hardening backlog rather than npm release failures.
