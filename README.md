# MCP Smart Typer

MCP Smart Typer is an experimental Windows-oriented MCP automation repository. The repository currently contains two distinct surfaces:

1. a schema-validated **development/mock MCP server** in TypeScript; and
2. experimental Python Windows UI-automation helpers that are built and tested separately.

## Release status

**No npm or Python package release is currently approved.** The active GitHub draft builds review candidates only. It does not publish to npm, PyPI, or GitHub Releases.

The npm entry point intentionally uses `MockNativeClient`. It does not control the host desktop. The Python native-helper package contains Windows automation experiments, but that native path is not yet bound to the npm server through a verified production contract.

## What is implemented

The development MCP server exposes mock-backed versions of:

- `detect_fields`
- `type_text`
- `get_field_value`
- `focus_field`

Requests are validated with Zod and responses are returned over MCP stdio. The mock adapter is useful for schema, client-integration, and safety-boundary testing without issuing real keyboard or mouse input.

The repository also contains Python prototypes for UI Automation, OCR, browser automation, and executable packaging. Those components remain experimental and require a Windows validation receipt before they may be described as production-ready.

## Build and validate from source

Requirements:

- Windows Server 2022 or Windows 10/11 for the full native-helper test surface
- Node.js 18 or 20
- npm 10.8.2
- Python 3.10–3.12

```powershell
git clone https://github.com/Zheke32174/mcp-smart-typer.git
cd mcp-smart-typer

npm install --global npm@10.8.2
npm ci
npm run lint
npm run typecheck
npm test
npm run build
```

Run the built mock MCP server:

```powershell
node packages/mcp-server-smart-typer/dist/index.js
```

Validate the Python package:

```powershell
cd packages/native-helpers
python -m pip install -e .
python -m black --check .
python -m isort --check-only .
python -m mypy src/ --ignore-missing-imports
python -m pytest -xvs .
```

## Candidate packaging

The release-candidate workflow verifies one matching version across the monorepo, npm package, Python package, and `v<version>` tag. It produces candidate artifacts and a checksum/source receipt but has **no publication authority**.

The intended npm package identity is:

```text
@mcp-smart-typer/server
```

Do not use older documentation that refers to `mcp-server-smart-typer` or the unrelated `modelcontextprotocol` organization as this repository's package owner.

## Security boundary

- The distributed TypeScript entry point is mock-backed.
- The npm package must not claim live Windows automation until an authenticated, bounded native transport is implemented and validated.
- Real keyboard, mouse, browser, OCR, and UIA operations belong to the Windows native-helper boundary.
- Generated candidates are evidence for review, not approval to publish or deploy.
- Do not put credentials, tokens, private topology, or sensitive UI data in issues or logs.

See [SECURITY.md](SECURITY.md) for vulnerability reporting and the current support boundary.

## Repository layout

```text
packages/mcp-server-smart-typer/  TypeScript MCP development server
packages/native-helpers/          Experimental Windows automation helpers
scripts/                           Release and repository-boundary validators
.github/workflows/                 Read-only CI and candidate-build workflows
```

## License

MIT. See [LICENSE](LICENSE).
