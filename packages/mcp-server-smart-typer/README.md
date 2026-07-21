# @mcp-smart-typer/server

A schema-validated **development/mock MCP server** for testing the MCP Smart Typer tool contract.

## Status

This package is a release candidate, not an approved registry release. The current entry point uses `MockNativeClient`; it does not type into or inspect the host desktop.

The separate Python package under `packages/native-helpers` contains experimental Windows UI-automation implementations. That native surface is not connected to this package through a verified production transport and is not part of the npm candidate.

## Tools

The mock server exposes:

- `detect_fields`
- `type_text`
- `get_field_value`
- `focus_field`

Inputs are validated with Zod and returned over MCP stdio. Mock responses are intended for client integration, schema validation, and safe development.

## Build and verify from source

From the repository root:

```powershell
npm install --global npm@10.9.3
npm ci --ignore-scripts --no-audit --no-fund
npm run lint:release --workspace @mcp-smart-typer/server
npm run typecheck:release --workspace @mcp-smart-typer/server
npm run build:release --workspace @mcp-smart-typer/server
npm run test:release --workspace @mcp-smart-typer/server
node packages/mcp-server-smart-typer/dist/index.js
```

## Candidate package lifecycle

Create and inspect a local candidate without publishing it:

```powershell
cd packages/mcp-server-smart-typer
npm pack --dry-run --json
npm pack
```

Install that reviewed tarball locally:

```powershell
npm install --global ./mcp-smart-typer-server-2.0.0.tgz
```

Update by retaining the prior tarball, verifying the new candidate, and installing the new tarball over it. Roll back by reinstalling the retained prior tarball. Remove the package with:

```powershell
npm uninstall --global @mcp-smart-typer/server
```

No registry installation command is documented until package ownership and publication authority are approved.

## Package contents

A candidate tarball is restricted to:

- `dist/`
- `README.md`
- `LICENSE`
- `package.json` and npm-required metadata

Source files, tests, scripts, lockfiles, and `node_modules` must not enter the tarball.

## Security boundary

This package does not grant MCP clients authority to enable host-level input or to self-authorize privileged operations. Live Windows automation must be mediated by a separately authenticated and constrained native adapter.

Do not send secrets or sensitive field contents to the mock server. Do not treat generated candidate artifacts as an approved release.

## Repository

- Source: https://github.com/Zheke32174/mcp-smart-typer
- Issues: https://github.com/Zheke32174/mcp-smart-typer/issues
- Security reporting: see the repository `SECURITY.md`

## License

MIT. See `LICENSE` in this package.
