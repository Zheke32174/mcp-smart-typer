#!/usr/bin/env node

/**
 * Prepare one reviewable npm-package version change.
 *
 * This script updates the monorepo and mock npm package version fields and emits
 * a preparation receipt. The experimental Python native helper has an
 * independent lifecycle and is intentionally not versioned by this command.
 *
 * This script does not create tags, publish packages, create releases, generate
 * compatibility claims, or grant publication authority.
 */

const crypto = require('crypto');
const fs = require('fs');
const path = require('path');
const { spawnSync } = require('child_process');

const root = path.resolve(__dirname, '..');
const targetVersion = process.argv[2];
const expectedRepository = 'git+https://github.com/Zheke32174/mcp-smart-typer.git';

function fail(message) {
  console.error(`release preparation refused: ${message}`);
  process.exit(1);
}

function runGit(args) {
  const result = spawnSync('git', args, {
    cwd: root,
    encoding: 'utf8',
    shell: false,
  });
  if (result.status !== 0) {
    fail(`git ${args.join(' ')} failed: ${(result.stderr || result.stdout || '').trim()}`);
  }
  return result.stdout.trim();
}

function canonicalJson(value) {
  const sort = (item) => {
    if (Array.isArray(item)) return item.map(sort);
    if (item && typeof item === 'object') {
      return Object.fromEntries(Object.keys(item).sort().map((key) => [key, sort(item[key])]));
    }
    return item;
  };
  return `${JSON.stringify(sort(value))}\n`;
}

function fsyncDirectoryBestEffort(directory) {
  let descriptor;
  try {
    descriptor = fs.openSync(directory, 'r');
    fs.fsyncSync(descriptor);
  } catch (error) {
    if (!['EACCES', 'EINVAL', 'EISDIR', 'ENOTSUP', 'EPERM'].includes(error.code)) throw error;
  } finally {
    if (descriptor !== undefined) fs.closeSync(descriptor);
  }
}

function atomicWrite(file, text) {
  const directory = path.dirname(file);
  fs.mkdirSync(directory, { recursive: true, mode: 0o700 });
  const temporary = path.join(
    directory,
    `.${path.basename(file)}.tmp.${process.pid}.${crypto.randomUUID().replaceAll('-', '')}`,
  );
  const descriptor = fs.openSync(temporary, 'wx', 0o600);
  try {
    const data = Buffer.from(text, 'utf8');
    let offset = 0;
    while (offset < data.length) {
      const written = fs.writeSync(descriptor, data, offset, data.length - offset, null);
      if (written <= 0) throw new Error('write made no progress');
      offset += written;
    }
    fs.fsyncSync(descriptor);
  } catch (error) {
    fs.closeSync(descriptor);
    fs.rmSync(temporary, { force: true });
    throw error;
  }
  fs.closeSync(descriptor);
  fs.renameSync(temporary, file);
  fsyncDirectoryBestEffort(directory);
}

function readJson(relative) {
  return JSON.parse(fs.readFileSync(path.join(root, relative), 'utf8'));
}

function digestFile(relative) {
  return crypto
    .createHash('sha256')
    .update(fs.readFileSync(path.join(root, relative)))
    .digest('hex');
}

if (!targetVersion || !/^\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?$/.test(targetVersion)) {
  fail('usage: node scripts/prepare-release.js <semver>');
}

const status = runGit(['status', '--porcelain=v1', '--untracked-files=all']);
if (status) fail('the Git worktree must be clean before changing release identity');

const sourceCommit = runGit(['rev-parse', '--verify', 'HEAD']);
if (!/^[0-9a-f]{40}$/.test(sourceCommit)) fail('HEAD is not one exact commit identity');

const rootPath = 'package.json';
const serverPath = 'packages/mcp-server-smart-typer/package.json';
const receiptPath = 'release-preparation.v1.json';

const rootPackage = readJson(rootPath);
const serverPackage = readJson(serverPath);

if (serverPackage.name !== '@mcp-smart-typer/server') {
  fail('npm package ownership is not @mcp-smart-typer/server');
}
if (serverPackage.repository?.url !== expectedRepository) {
  fail('npm package repository identity is not the owned GitHub repository');
}

const currentVersions = [rootPackage.version, serverPackage.version];
if (!currentVersions.every((value) => value === currentVersions[0])) {
  fail(`current npm package versions disagree: ${currentVersions.join(', ')}`);
}
if (currentVersions[0] === targetVersion) fail(`version is already ${targetVersion}`);

rootPackage.version = targetVersion;
serverPackage.version = targetVersion;

atomicWrite(path.join(root, rootPath), `${JSON.stringify(rootPackage, null, 2)}\n`);
atomicWrite(path.join(root, serverPath), `${JSON.stringify(serverPackage, null, 2)}\n`);

const receipt = {
  schema: 'mcp-smart-typer.release-preparation/v2',
  sourceCommit,
  previousVersion: currentVersions[0],
  targetVersion,
  repository: 'https://github.com/Zheke32174/mcp-smart-typer',
  packageName: '@mcp-smart-typer/server',
  authority: 'none',
  nativeHelperVersionChanged: false,
  files: [rootPath, serverPath].map((file) => ({
    path: file,
    sha256: digestFile(file),
  })),
  requiredNextSteps: [
    'review the complete npm-package diff',
    'run npm run validate-cicd and the maintained Node release matrix',
    'review native-helper diagnostics separately only when native-helper inputs changed',
    'commit the reviewed npm-package version change',
    'create an exact matching version tag only after review',
    'review the candidate receipt before any separate publication decision',
  ],
};
atomicWrite(path.join(root, receiptPath), canonicalJson(receipt));

console.log(`Prepared reviewable npm package version change ${currentVersions[0]} -> ${targetVersion}`);
console.log(`Source commit: ${sourceCommit}`);
console.log(`Receipt: ${receiptPath}`);
console.log('The experimental native-helper version was not changed.');
console.log('No tag, package publication, GitHub Release, or compatibility claim was created.');
