# Release and Deployment Guide

This document describes the CI/CD pipeline and release process for MCP Smart Typer.

## Overview

The project uses GitHub Actions for automated CI/CD with the following key features:

- **Multi-platform testing** (TypeScript/Node.js and Python)
- **Automated building** of Python executables using PyInstaller
- **npm package publishing** as `@modelcontextprotocol/server-smart-typer`
- **GitHub releases** with automated release notes
- **MCP specification compliance** validation

## CI/CD Pipeline

### Jobs

1. **test-node**: Tests TypeScript code across Node.js 18.x and 20.x
2. **test-python**: Tests Python code across Python 3.8-3.12
3. **build-python-executable**: Creates Windows executable using PyInstaller
4. **publish-npm**: Publishes to npm registry with proper naming
5. **create-release**: Creates GitHub releases with assets

### Triggers

- **Pull Requests**: Full test suite runs on PRs to `main` and `develop`
- **Main Branch**: Publishes beta versions to npm with `-beta.timestamp` suffix
- **Version Tags**: Publishes stable releases and creates GitHub releases

## Release Process

### 1. Prepare Release

Use the automated release preparation script:

```bash
# Update version numbers and generate changelog
npm run prepare-release 2.1.0
```

This script:
- Updates version in all `package.json` files
- Updates version in `pyproject.toml`
- Validates MCP specification compliance
- Generates changelog entries
- Ensures proper keywords and metadata

### 2. Review and Commit Changes

```bash
# Review the automated changes
git diff

# Commit the release preparation
git add -A
git commit -m "chore: prepare release v2.1.0"
```

### 3. Create and Push Tag

```bash
# Create version tag
git tag v2.1.0

# Push tag to trigger release
git push origin v2.1.0
```

### 4. Automated Release

The CI/CD pipeline will:
1. Run all tests
2. Build Python executable
3. Publish to npm as `@modelcontextprotocol/server-smart-typer`
4. Create GitHub release with:
   - Generated release notes
   - Windows executable attachment
   - Installation instructions

## Package Publishing

### npm Package Structure

The published package includes:
- **TypeScript server** (`dist/` folder)
- **Python executable** (`bin/mcp-uia-server.exe`)
- **Documentation** (README, LICENSE)
- **MCP compliance metadata**

### Package Name

Published as: `@modelcontextprotocol/server-smart-typer`

### Installation

Users can install via:

```bash
# Global installation
npm install -g @modelcontextprotocol/server-smart-typer

# Or use the executables directly
npx @modelcontextprotocol/server-smart-typer
```

## MCP Specification Compliance

### Required Elements

- **MCP SDK dependency**: `@modelcontextprotocol/sdk`
- **Proper keywords**: `mcp`, `model-context-protocol`
- **Specification version**: Declared in `mcpSpecVersion` field
- **Resource management**: Proper tool and resource declarations
- **Error handling**: MCP-compliant error responses

### Validation

The release script automatically validates:
- Required dependencies are present
- MCP keywords are included
- Specification version is declared
- Package structure is correct

## Security and Secrets

### Required Secrets

Configure these in GitHub repository settings:

- **`NPM_TOKEN`**: npm registry authentication token
- **`GITHUB_TOKEN`**: Automatically provided by GitHub Actions

### NPM Token Setup

1. Create npm account and login
2. Generate access token with publish permissions
3. Add to GitHub Secrets as `NPM_TOKEN`

## Versioning Strategy

### Semantic Versioning

- **Major** (X.0.0): Breaking changes, MCP spec updates
- **Minor** (x.Y.0): New features, backward compatible
- **Patch** (x.y.Z): Bug fixes, security updates

### Beta Releases

- Main branch pushes create beta versions: `2.1.0-beta.20241215123456`
- Tagged releases create stable versions: `2.1.0`

## Troubleshooting

### Common Issues

1. **npm publish fails**: Check `NPM_TOKEN` secret
2. **Python build fails**: Verify dependencies in `requirements.txt`
3. **Tests fail**: Check Node.js/Python version compatibility
4. **Release notes empty**: Ensure git tags exist

### Debugging

Check GitHub Actions logs for detailed error information:
1. Go to repository → Actions tab
2. Click on failed workflow run
3. Expand failed job steps
4. Review error messages and logs

## Manual Release Process

If automated release fails, you can manually:

### 1. Build Python Executable

```bash
cd packages/native-helpers
pip install -r requirements.txt
python -m grpc_tools.protoc -I ./proto --python_out=./src/generated --grpc_python_out=./src/generated ./proto/ui_automation.proto
pyinstaller build_uia_server.spec --clean --noconfirm
```

### 2. Build and Publish npm Package

```bash
# Build TypeScript
pnpm build

# Update package name for publishing
cd packages/mcp-server-smart-typer
# Edit package.json to set name to "@modelcontextprotocol/server-smart-typer"

# Publish
npm publish
```

### 3. Create GitHub Release

1. Go to GitHub repository → Releases
2. Click "Create a new release"
3. Choose tag version
4. Add release notes (see CHANGELOG.md)
5. Attach `mcp-uia-server.exe`
6. Publish release

## Post-Release

After successful release:

1. **Verify npm package**: Check on npmjs.com
2. **Test installation**: `npm install -g @modelcontextprotocol/server-smart-typer`
3. **Update documentation**: Ensure README reflects new version
4. **Announce release**: Share with MCP community
5. **Monitor issues**: Watch for user feedback and bug reports

## Future Improvements

- **Multi-platform builds**: Add macOS and Linux support
- **Automated testing**: E2E tests with real UI applications
- **Performance monitoring**: Runtime metrics and profiling
- **Security scanning**: Automated vulnerability checks
- **Documentation generation**: API docs from TypeScript types
