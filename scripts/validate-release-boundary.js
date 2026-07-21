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
const packageLock = json('package-lock.json');
const serverPackage = json('packages/mcp-server-smart-typer/package.json');
const serverReadme = text('packages/mcp-server-smart-typer/README.md');
const serverLicense = text('packages/mcp-server-smart-typer/LICENSE');
const pyproject = text('packages/native-helpers/pyproject.toml');
const ci = text('.github/workflows/ci.yml');
const nativeDiagnostics = text('.github/workflows/python-diagnostics.yml');
const candidate = text('.github/workflows/release-candidate.yml');
const preparation = text('scripts/prepare-release.js');
const inspected = [
  JSON.stringify(serverPackage),
  serverReadme,
  pyproject,
  ci,
  nativeDiagnostics,
  candidate,
  preparation,
]
  .join('\n')
  .toLowerCase();

const expectedRepository = 'github.com/zheke32174/mcp-smart-typer';
assert(serverPackage.name === '@mcp-smart-typer/server', 'npm package name changed ownership');
for (const value of [
  serverPackage.repository?.url,
  serverPackage.bugs?.url,
  serverPackage.homepage,
]) {
  assert(
    String(value || '').toLowerCase().includes(expectedRepository),
    'npm metadata is not bound to the owned repository',
  );
}
assert(
  pyproject.toLowerCase().includes(expectedRepository),
  'Python metadata is not bound to the owned repository',
);
for (const forbidden of [
  '@modelcontextprotocol/server-smart-typer',
  'github.com/modelcontextprotocol/server-smart-typer',
  'github.com/mcp-smart-typer/mcp-smart-typer',
  'team@mcp-smart-typer.dev',
]) {
  assert(!inspected.includes(forbidden), `false provenance remains: ${forbidden}`);
}

assert(
  rootPackage.version && rootPackage.version === serverPackage.version,
  `root and npm package versions differ: ${rootPackage.version}, ${serverPackage.version}`,
);
assert(rootPackage.packageManager === 'npm@10.9.3', 'packageManager must identify npm 10.9.3');
assert(rootPackage.engines?.node === '>=22.0.0', 'Node engine floor must be 22 or newer');
assert(rootPackage.engines?.npm === '>=10.9.3', 'npm engine floor must be 10.9.3 or newer');
assert(packageLock.lockfileVersion === 3, 'package-lock.json must be lockfile version 3');
assert(!Object.hasOwn(rootPackage.scripts || {}, 'version'), 'implicit npm version mutation is enabled');
assert(
  rootPackage.scripts?.['prepare-release'] === 'node scripts/prepare-release.js',
  'release preparation is not explicit',
);
assert(
  rootPackage.scripts?.['validate-cicd'] === 'node scripts/validate-release-boundary.js',
  'package validation does not use the canonical policy script',
);
for (const [name, command] of Object.entries(rootPackage.scripts || {})) {
  assert(!String(command).includes('pnpm'), `root script ${name} still invokes pnpm`);
}

assert(serverLicense.startsWith('MIT License'), 'package-local MIT license is missing');
assert(serverPackage.main === 'dist/index.js', 'npm main entry is not the bounded build');
assert(serverPackage.bin?.['mcp-server-smart-typer'] === 'dist/index.js', 'npm bin entry is not bounded');
for (const script of ['build:release', 'lint:release', 'typecheck:release', 'test:release']) {
  assert(serverPackage.scripts?.[script], `bounded npm script is missing: ${script}`);
}
const allowedRuntimeDependencies = new Set(['@modelcontextprotocol/sdk', 'zod']);
for (const dependency of Object.keys(serverPackage.dependencies || {})) {
  assert(allowedRuntimeDependencies.has(dependency), `native dependency escaped npm package: ${dependency}`);
}
for (const requiredFile of ['dist/', 'README.md', 'LICENSE']) {
  assert((serverPackage.files || []).includes(requiredFile), `npm files allowlist omits ${requiredFile}`);
}
assert(serverReadme.includes('MockNativeClient'), 'package README does not disclose mock execution');
assert(
  serverReadme.includes('npm uninstall --global @mcp-smart-typer/server'),
  'package removal instructions are missing',
);

assert(ci.includes('permissions:\n  contents: read'), 'strict npm CI is not read-only');
for (const forbidden of [
  'npm publish',
  'NODE_AUTH_TOKEN',
  'secrets.NPM_TOKEN',
  'action-gh-release',
  'pnpm',
  'setup-python',
  'native-helpers',
  'PyInstaller',
]) {
  assert(!ci.includes(forbidden), `strict npm CI contains unrelated or privileged behavior: ${forbidden}`);
}
assert(!ci.includes("tags:\n      - 'v*'"), 'ordinary CI is also acting as the tag workflow');
assert(ci.includes('npm ci --ignore-scripts --no-audit --no-fund'), 'ordinary CI install is not bounded');
for (const command of [
  'npm run lint:release --workspace @mcp-smart-typer/server',
  'npm run typecheck:release --workspace @mcp-smart-typer/server',
  'npm run build:release --workspace @mcp-smart-typer/server',
  'npm run test:release --workspace @mcp-smart-typer/server',
  'npm pack --dry-run --json',
  'node scripts/validate-release-boundary.js',
  'node-version: [22.x, 24.x]',
  'release-policy-${{ github.sha }}',
]) {
  assert(ci.includes(command), `strict npm CI invariant missing: ${command}`);
}
assert(ci.includes('if-no-files-found: error'), 'missing npm candidate output does not fail CI');

assert(nativeDiagnostics.includes("'packages/native-helpers/**'"), 'native diagnostics are not path-scoped');
assert(nativeDiagnostics.includes('permissions:\n  contents: read'), 'native diagnostics are not read-only');
assert(nativeDiagnostics.includes('continue-on-error: true'), 'native diagnostics can block npm readiness');
assert(nativeDiagnostics.includes('persist-credentials: false'), 'native diagnostic checkout persists credentials');
assert(nativeDiagnostics.includes('python -m pytest -xvs tests'), 'focused native tests are not recorded');
assert(
  nativeDiagnostics.includes('Native helper remains experimental and is not part of the npm tarball.'),
  'native diagnostic boundary is not explicit',
);
for (const forbidden of ['npm publish', 'action-gh-release', 'secrets.NPM_TOKEN', 'PyInstaller']) {
  assert(!nativeDiagnostics.includes(forbidden), `native diagnostics contain release behavior: ${forbidden}`);
}

assert(candidate.includes("tags:\n      - 'v*'"), 'candidate workflow is not tag-only');
assert(candidate.includes("NODE_VERSION: '22.x'"), 'candidate workflow does not use maintained Node LTS');
assert(candidate.includes("NPM_VERSION: '10.9.3'"), 'candidate workflow does not use the locked npm');
for (const required of [
  'git merge-base --is-ancestor "$GITHUB_SHA" refs/remotes/origin/main',
  "os.environ['GITHUB_REF_NAME'] != f'v{version}'",
  "'source_commit': os.environ['GITHUB_SHA']",
  "'publication_authority': 'none'",
  "'native_helper_included': False",
  "'package_lock_sha256'",
  "'package_manifest_sha256'",
  'npm ci --ignore-scripts --no-audit --no-fund',
  'npm run lint:release --workspace @mcp-smart-typer/server',
  'npm run typecheck:release --workspace @mcp-smart-typer/server',
  'npm run build:release --workspace @mcp-smart-typer/server',
  'npm run test:release --workspace @mcp-smart-typer/server',
  'npm pack --json',
  'SHA256SUMS.txt',
  'BUILD-RECEIPT.json',
]) {
  assert(candidate.includes(required), `candidate invariant missing: ${required}`);
}
for (const forbidden of [
  'npm publish',
  'action-gh-release',
  'secrets.NPM_TOKEN',
  'pnpm',
  'setup-python',
  'native-helpers',
  'PyInstaller',
]) {
  assert(!candidate.includes(forbidden), `candidate workflow contains retired behavior: ${forbidden}`);
}

for (const required of [
  "authority: 'none'",
  'nativeHelperVersionChanged: false',
  "runGit(['status', '--porcelain=v1', '--untracked-files=all'])",
  "runGit(['rev-parse', '--verify', 'HEAD'])",
  'release-preparation.v2',
  'The experimental native-helper version was not changed.',
]) {
  assert(preparation.includes(required), `release preparation invariant missing: ${required}`);
}
for (const forbidden of [
  "const pythonPath = 'packages/native-helpers/pyproject.toml'",
  'git tag ',
  'npm publish',
  'Full compatibility',
  'Enhanced security',
]) {
  assert(!preparation.includes(forbidden), `release preparation contains retired behavior: ${forbidden}`);
}

const expectedActions = [
  'actions/checkout@34e114876b0b11c390a56381ad16ebd13914f8d5',
  'actions/setup-node@49933ea5288caeca8642d1e84afbd3f7d6820020',
  'actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065',
  'actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02',
];
for (const action of expectedActions) {
  assert(
    ci.includes(action) || nativeDiagnostics.includes(action) || candidate.includes(action),
    `pinned action missing: ${action}`,
  );
}
for (const workflow of [ci, nativeDiagnostics, candidate]) {
  assert(
    !/uses:\s+actions\/[A-Za-z0-9_.-]+@v\d+/m.test(workflow),
    'moving actions/* version tag remains',
  );
  for (const match of workflow.matchAll(/uses:\s+(actions\/[A-Za-z0-9_.-]+)@([^\s]+)/g)) {
    assert(/^[0-9a-f]{40}$/.test(match[2]), `${match[1]} is not pinned to one commit`);
  }
}

if (failures.length) {
  console.error('Release-boundary validation failed:');
  for (const failure of failures) console.error(`- ${failure}`);
  process.exit(1);
}
console.log(
  'PASS: bounded mock npm package, package-local license, independent native diagnostics, independent release identities, read-only CI, immutable actions, and tag-only candidate generation',
);
