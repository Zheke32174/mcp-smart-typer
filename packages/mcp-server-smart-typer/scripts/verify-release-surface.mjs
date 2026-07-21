import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const root = join(here, '..');
const packageJson = JSON.parse(await readFile(join(root, 'package.json'), 'utf8'));
const entrypoint = await readFile(join(root, 'src', 'index.ts'), 'utf8');
const server = await readFile(join(root, 'src', 'simple-server.ts'), 'utf8');
const releaseConfig = JSON.parse(await readFile(join(root, 'tsconfig.release.json'), 'utf8'));

assert.equal(packageJson.name, '@mcp-smart-typer/server');
assert.equal(packageJson.main, 'dist/index.js');
assert.equal(packageJson.bin['mcp-server-smart-typer'], 'dist/index.js');
assert.deepEqual(packageJson.files, ['dist/', 'README.md', 'LICENSE']);
assert.match(packageJson.engines.node, /^>=22/);
assert.equal(packageJson.scripts.build, 'npm run build:release');
assert.equal(packageJson.scripts.lint, 'npm run lint:release');
assert.equal(packageJson.scripts.typecheck, 'npm run typecheck:release');
assert.ok(!Object.hasOwn(packageJson.dependencies, '@tensorflow/tfjs-node'));
assert.ok(!Object.hasOwn(packageJson.dependencies, 'playwright'));
assert.ok(!Object.hasOwn(packageJson.dependencies, '@grpc/grpc-js'));

assert.match(entrypoint, /import '\.\/simple-server\.js';/);
assert.doesNotMatch(entrypoint, /enhanced-server|security-control|permission-manager/);
assert.match(server, /new MockNativeClient\(\)/);
assert.doesNotMatch(server, /SecurityManager|PermissionManager|RollbackManager/);

const included = new Set(releaseConfig.include);
for (const expected of [
  'src/index.ts',
  'src/simple-server.ts',
  'src/schemas/index.ts',
  'src/utils/job-manager.ts',
  'src/utils/logger.ts',
  'src/utils/mock-native-client.ts',
]) {
  assert.ok(included.has(expected), `release TypeScript boundary omits ${expected}`);
}

console.log('PASS: npm release surface is bounded to the mock-backed server');
