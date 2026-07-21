# @mcp-smart-typer/server

A schema-validated **development/mock MCP server** for testing the MCP Smart Typer tool contract.

## Status

This package is a release candidate, not an approved registry release. The current entry point uses `MockNativeClient`; it does not type into or inspect the host desktop.

The separate Python package under `packages/native-helpers` contains experimental Windows UI-automation implementations. That native surface is not yet connected to this package through a verified production transport.

## Tools

The mock server exposes:

- `detect_fields`
- `type_text`
- `get_field_value`
- `focus_field`

Inputs are validated with Zod and returned over MCP stdio. Mock responses are intended for client integration, schema validation, and safe development.

## Build from source

From the repository root:

```powershell
npm install --global npm@10.8.2
npm ci
npm run lint
npm run typecheck
npm test
npm run build
node packages/mcp-server-smart-typer/dist/index.js
```

## Package contents

A candidate tarball is restricted to:

- `dist/`
- `README.md`
- `LICENSE`
- `package.json` and npm-required metadata

Inspect it before any publication decision:

```powershell
cd packages/mcp-server-smart-typer
npm pack --dry-run
```

## Security boundary

This package does not grant MCP clients authority to enable host-level input or to self-authorize privileged operations. Live Windows automation must be mediated by a separately authenticated and constrained native adapter.

Do not send secrets or sensitive field contents to the mock server. Do not treat generated candidate artifacts as an approved release.

## Repository

- Source: https://github.com/Zheke32174/mcp-smart-typer
- Issues: https://github.com/Zheke32174/mcp-smart-typer/issues
- Security reporting: see the repository `SECURITY.md`

## License

MIT.
