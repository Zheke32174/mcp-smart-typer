# Public Release-Readiness Checkpoint

Repository: `Zheke32174/mcp-smart-typer`  
Draft branch: `workflow/verified-publication-v1`  
Draft pull request: `#4`  
Default branch changed: no  
Registry publication authority: none

## Last reviewed heads

- Prior exact-head diagnostics: `c449266a47b1b5650c32d5994b0b348e2f8eabbd`
- Mock-only npm boundary repair: `ed089f1e04bae3c861f92151e6ecbe89c49b1ee4`
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
- Moved strict Node release validation to Linux Node 22/24 to eliminate Windows checkout conversion as a false lint signal.
- Retained Windows Python 3.10/3.11/3.12 checks as nonblocking experimental diagnostics with uploaded Black, mypy, and pytest evidence.
- Removed the native executable build from the npm release gate; it requires a separate future artifact policy and live Windows validation.
- Refreshed `package-lock.json`, formatted the bounded TypeScript surface, removed unused response-schema imports, ran lint/typecheck/build/contract tests, published one coherent repair commit, and removed the temporary writer.

## Validation receipts

At head `c449266a47b1b5650c32d5994b0b348e2f8eabbd`:

- release policy passed;
- npm lock consistency passed;
- Python source compilation passed on 3.10, 3.11, and 3.12;
- Node lint reached source and produced durable artifacts;
- Node failures contained 10,685 cross-platform CRLF findings, one invalid rule identity, and remaining legacy-module lint debt;
- Python formatting still included Windows checkout/generated-file noise;
- mypy reported 380 errors in the experimental native implementation;
- pytest collection failed in a legacy top-level demonstration class because an instance decorator was used as a class decorator.

These diagnostics changed the release decision: the native helper cannot honestly gate or ship inside the mock npm package.

The one-shot mock-boundary transaction at head `ed089f1e04bae3c861f92151e6ecbe89c49b1ee4` completed its internal npm lock refresh, formatting, release lint, release typecheck, release build, contract test, patch check, branch publication, and self-removal. Its bot-authored head produced `action_required` placeholders with zero jobs, so this ledger commit supplies the normal exact-head CI trigger.

## External practices applied

- npm package allowlisting through `package.json#files`; npm otherwise defaults to broad inclusion.
- Full-SHA Action references and least-privilege read-only validation.
- Node 22 and 24 LTS release testing; Node 20 is EOL as of March 24, 2026.
- Repository-level LF normalization consistent with Prettier's Git-oriented line-ending guidance.
- Separate release gates for a distributable package and an experimental platform-specific subsystem.
- Candidate-only builds until package ownership and a separately reviewed trusted-publishing workflow exist.

Primary references:

- https://docs.npmjs.com/files/package.json/
- https://docs.github.com/en/actions/reference/security/secure-use
- https://nodejs.org/en/about/previous-releases
- https://prettier.io/docs/options#end-of-line

## Open blockers

1. The mock npm package requires a green non-bot exact-head receipt for Node 22 and 24: lock install, bounded lint, bounded typecheck, bounded build, contract test, and tarball inspection.
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

Inspect CI triggered by this ledger commit. If Node 22/24 passes, retain `HOLD` only for registry ownership and publication authority. If it fails, repair only the exact bounded mock-package defect on this same branch. Treat native Python findings as a separate experimental-hardening backlog rather than npm release failures.
