#!/usr/bin/env node

/**
 * Static release-boundary validation.
 *
 * This script deliberately does not install dependencies, build packages, publish
 * artifacts, or contact a registry. It validates that committed metadata and
 * workflows preserve repository ownership and fail-closed test behavior.
 */

const fs = require('fs');

const failures = [];

function requireFile(file) {
  if (!fs.existsSync(file)) {
    failures.push(`required file missing: ${file}`);
    return '';
  }
  return fs.readFileSync(file, 'utf8');
}

function assert(condition, message) {
  if (!condition) failures.push(message);
}

function readJson(file) {
  const text = requireFile(file);
  if (!text) return {};
  try {
    return JSON.parse(text);
  } catch (error) {
    failures.push(`invalid JSON in ${file}: ${error.message}`);
    return {};
  }
}

const rootPackage = readJson('package.json');
const serverPackage = readJson('packages/mcp-server-smart-typer/package.json');
const pyproject = requireFile('packages/native-helpers/pyproject.toml');
const ci = requireFile('.github/workflows/ci.yml');
const candidate = requireFile('.github/workflows/release-candidate.yml');

const expectedRepository = 'github.com/zheke32174/mcp-smart-typer';
const forbiddenProvenance = [
  '@modelcontextprotocol/server-smart-typer',
  'github.com/modelcontextprotocol/server-smart-typer',
  'github.com/mcp-smart-typer/mcp-smart-typer',
  'team@mcp-smart-typer.dev',
];
const inspected = [JSON.stringify(serverPackage), pyproject, ci, candidate]
  .join('\n')
  .toLowerCase();

assert(serverPackage.name === '@mcp-smart-typer/server', 'npm package name must remain @mcp-smart-typer/server');
assert(
  String(serverPackage.repository?.url || '').toLowerCase().includes(expectedRepository),
  'npm repository URL must identify Zheke32174/mcp-smart-typer'
);
assert(
  String(serverPackage.bugs?.url || '').toLowerCase().includes(expectedRepository),
  'npm issue URL must identify Zheke32174/mcp-smart-typer'
);
assert(
  String(serverPackage.homepage || '').toLowerCase().includes(expectedRepository),
  'npm homepage must identify Zheke32174/mcp-smart-typer'
);
assert(
  pyproject.toLowerCase().includes('github.com/zheke32174/mcp-smart-typer'),
  'Python project URLs must identify Zheke32174/mcp-smart-typer'
);
for (const value of forbiddenProvenance) {
  assert(!inspected.includes(value.toLowerCase()), `forbidden false provenance remains: ${value}`);
}

const pythonVersionMatch = pyproject.match(/^version = "([^"]+)"$/m);
assert(Boolean(pythonVersionMatch), 'Python package version is missing');
const versions = [rootPackage.version, serverPackage.version, pythonVersionMatch?.[1]];
assert(versions.every((value) => value === versions[0]), `package versions differ: ${versions.join(', ')}`);

assert(ci.includes('permissions:\n  contents: read'), 'ordinary CI must have read-only contents permission');
assert(!ci.includes('publish-npm'), 'ordinary CI must not contain an npm publication job');
assert(!ci.includes('npm publish'), 'ordinary CI must not publish npm packages');
assert(!ci.includes('NODE_AUTH_TOKEN'), 'ordinary CI must not receive an npm token');
assert(!ci.includes('secrets.NPM_TOKEN'), 'ordinary CI must not reference an npm token secret');
assert(!ci.includes('action-gh-release'), 'ordinary CI must not create GitHub releases');
assert(!ci.includes("tags:\n      - 'v*'"), 'ordinary CI must not run as the release-tag workflow');
assert(ci.includes('python -m pytest -xvs .'), 'ordinary CI must run Python tests directly');
assert(!ci.includes('|| echo'), 'ordinary CI must not mask command failures');
assert(ci.includes('if-no-files-found: error'), 'candidate artifact upload must fail when output is missing');

assert(candidate.includes("tags:\n      - 'v*'"), 'candidate construction must be restricted to immutable version tags');
assert(candidate.includes("os.environ['GITHUB_REF_NAME'] != f'v{version}'"), 'candidate workflow must bind tag to package version');
assert(candidate.includes("'source_commit': os.environ['GITHUB_SHA']"), 'candidate receipt must bind the exact source commit');
assert(candidate.includes("'publication_authority': 'none'"), 'candidate receipt must state that it has no publication authority');
assert(!candidate.includes('npm publish'), 'candidate workflow must not publish npm packages');
assert(!candidate.includes('action-gh-release'), 'candidate workflow must not create a GitHub release');
assert(!candidate.includes('secrets.NPM_TOKEN'), 'candidate workflow must not receive npm credentials');
assert(candidate.includes('SHA256SUMS.txt'), 'candidate workflow must emit checksums');
assert(candidate.includes('BUILD-RECEIPT.json'), 'candidate workflow must emit a build receipt');

const pinnedActions = [
  'actions/checkout@34e114876b0b11c390a56381ad16ebd13914f8d5',
  'actions/setup-node@49933ea5288caeca8642d1e84afbd3f7d6820020',
  'actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065',
  'actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02',
];
for (const action of pinnedActions) {
  assert(ci.includes(action) || candidate.includes(action), `required pinned action is missing: ${action}`);
}
assert(
  candidate.includes('actions/download-artifact@d3f86a106a0bac45b974a628896c90dbdf5c8093'),
  'candidate download action must be commit-pinned'
);
for (const workflow of [ci, candidate]) {
  assert(!/uses:\s+actions\/[A-Za-z0-9_.-]+@v\d+/m.test(workflow), 'moving actions/* major-version tag remains');
  const actionReferences = [...workflow.matchAll(/uses:\s+(actions\/[A-Za-z0-9_.-]+)@([^\s]+)/g)];
  for (const [, name, revision] of actionReferences) {
    assert(/^[0-9a-f]{40}$/.test(revision), `${name} is not pinned to a lowercase 40-character commit`);
  }
}

if (failures.length) {
  console.error('Release-boundary validation failed:');
  for (const failure of failures) console.error(`- ${failure}`);
  process.exit(1);
}

console.log('PASS: repository identity, fail-closed tests, read-only CI, pinned actions, and candidate-only tag workflow');
