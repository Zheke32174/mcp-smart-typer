#!/usr/bin/env node

const fs = require('fs');
const failures = [];

function text(file) {
  if (!fs.existsSync(file)) {
    failures.push(`required file missing: ${file}`);
    return '';
  }
  return fs.readFileSync(file, 'utf8');
}

function json(file) {
  try {
    return JSON.parse(text(file));
  } catch (error) {
    failures.push(`invalid JSON in ${file}: ${error.message}`);
    return {};
  }
}

function assert(condition, message) {
  if (!condition) failures.push(message);
}

const rootPackage = json('package.json');
const serverPackage = json('packages/mcp-server-smart-typer/package.json');
const pyproject = text('packages/native-helpers/pyproject.toml');
const ci = text('.github/workflows/ci.yml');
const candidate = text('.github/workflows/release-candidate.yml');
const preparation = text('scripts/prepare-release.js');
const inspected = [JSON.stringify(serverPackage), pyproject, ci, candidate, preparation]
  .join('\n')
  .toLowerCase();

const expectedRepository = 'github.com/zheke32174/mcp-smart-typer';
assert(serverPackage.name === '@mcp-smart-typer/server', 'npm package name changed ownership');
for (const value of [
  serverPackage.repository?.url,
  serverPackage.bugs?.url,
  serverPackage.homepage,
]) {
  assert(String(value || '').toLowerCase().includes(expectedRepository), 'npm metadata is not bound to the owned repository');
}
assert(pyproject.toLowerCase().includes(expectedRepository), 'Python metadata is not bound to the owned repository');
for (const forbidden of [
  '@modelcontextprotocol/server-smart-typer',
  'github.com/modelcontextprotocol/server-smart-typer',
  'github.com/mcp-smart-typer/mcp-smart-typer',
  'team@mcp-smart-typer.dev',
]) {
  assert(!inspected.includes(forbidden), `false provenance remains: ${forbidden}`);
}

const pythonVersion = pyproject.match(/^version = "([^"]+)"$/m)?.[1];
const versions = [rootPackage.version, serverPackage.version, pythonVersion];
assert(versions.every((value) => value && value === versions[0]), `package versions differ: ${versions.join(', ')}`);
assert(!Object.hasOwn(rootPackage.scripts || {}, 'version'), 'implicit npm version lifecycle mutation is enabled');
assert(rootPackage.scripts?.['prepare-release'] === 'node scripts/prepare-release.js', 'release preparation is not explicit');
assert(rootPackage.scripts?.['validate-cicd'] === 'node scripts/validate-release-boundary.js', 'package validation does not use the canonical policy script');

assert(ci.includes('permissions:\n  contents: read'), 'ordinary CI is not read-only');
for (const forbidden of ['publish-npm', 'npm publish', 'NODE_AUTH_TOKEN', 'secrets.NPM_TOKEN', 'action-gh-release', '|| echo']) {
  assert(!ci.includes(forbidden), `ordinary CI contains forbidden behavior: ${forbidden}`);
}
assert(!ci.includes("tags:\n      - 'v*'"), 'ordinary CI is also acting as the tag workflow');
assert(ci.includes('python -m pytest -xvs .'), 'Python tests are not fail-closed');
assert(ci.includes('if-no-files-found: error'), 'missing candidate outputs do not fail CI');
assert(ci.includes('node scripts/validate-release-boundary.js'), 'ordinary CI does not run the canonical policy validator');

assert(candidate.includes("tags:\n      - 'v*'"), 'candidate workflow is not tag-only');
assert(candidate.includes("os.environ['GITHUB_REF_NAME'] != f'v{version}'"), 'candidate tag is not bound to package version');
assert(candidate.includes("'source_commit': os.environ['GITHUB_SHA']"), 'candidate receipt is not bound to source commit');
assert(candidate.includes("'publication_authority': 'none'"), 'candidate receipt claims publication authority');
assert(candidate.includes('node scripts/validate-release-boundary.js'), 'candidate workflow does not run the canonical policy validator');
for (const forbidden of ['npm publish', 'action-gh-release', 'secrets.NPM_TOKEN']) {
  assert(!candidate.includes(forbidden), `candidate workflow contains forbidden behavior: ${forbidden}`);
}
for (const required of ['SHA256SUMS.txt', 'BUILD-RECEIPT.json']) {
  assert(candidate.includes(required), `candidate workflow does not emit ${required}`);
}

for (const required of [
  "authority: 'none'",
  "runGit(['status', '--porcelain=v1', '--untracked-files=all'])",
  "runGit(['rev-parse', '--verify', 'HEAD'])",
  'release-preparation.v1.json',
]) {
  assert(preparation.includes(required), `release preparation invariant missing: ${required}`);
}
for (const forbidden of ['git tag ', 'npm publish', 'Full compatibility', 'Enhanced security']) {
  assert(!preparation.includes(forbidden), `release preparation contains forbidden behavior or claim: ${forbidden}`);
}

const expectedActions = [
  'actions/checkout@34e114876b0b11c390a56381ad16ebd13914f8d5',
  'actions/setup-node@49933ea5288caeca8642d1e84afbd3f7d6820020',
  'actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065',
  'actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02',
  'actions/download-artifact@d3f86a106a0bac45b974a628896c90dbdf5c8093',
];
for (const action of expectedActions) {
  assert(ci.includes(action) || candidate.includes(action), `pinned action missing: ${action}`);
}
for (const workflow of [ci, candidate]) {
  assert(!/uses:\s+actions\/[A-Za-z0-9_.-]+@v\d+/m.test(workflow), 'moving actions/* version tag remains');
  for (const match of workflow.matchAll(/uses:\s+(actions\/[A-Za-z0-9_.-]+)@([^\s]+)/g)) {
    assert(/^[0-9a-f]{40}$/.test(match[2]), `${match[1]} is not pinned to one commit`);
  }
}

if (failures.length) {
  console.error('Release-boundary validation failed:');
  for (const failure of failures) console.error(`- ${failure}`);
  process.exit(1);
}
console.log('PASS: owned provenance, explicit preparation, fail-closed tests, read-only CI, pinned actions, and candidate-only tags');
