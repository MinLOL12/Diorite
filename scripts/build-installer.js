#!/usr/bin/env node
/**
 * Diorite — ONE command to build the installer EXE.
 *
 *   node scripts/build-installer.js        (or: npm run make:exe)
 *
 * That's it. It produces ONE file:
 *   dist/installer/Diorite-Setup-<version>-x64.exe   (Windows)
 *   dist/installer/Diorite-<version>.AppImage        (Linux)
 *   dist/installer/Diorite-<version>.dmg             (macOS)
 *
 * Users then just double-click that file. No Python, no Node, no Java
 * needed on their machine — everything is bundled inside.
 *
 * Options:
 *   --fail-fast   stop immediately on any error instead of continuing
 *                 past non-critical steps
 */
const { execSync, spawnSync } = require('child_process');
const fs = require('fs');
const os = require('os');
const path = require('path');

const root = path.join(__dirname, '..');
const FAIL_FAST = process.argv.includes('--fail-fast');
const IS_WIN = os.platform() === 'win32';

let totalSteps = 5;
let step = 0;

function log(msg) {
  console.log(`\x1b[36m[Diorite]\x1b[0m ${msg}`);
}

function banner(msg) {
  step += 1;
  console.log('');
  console.log(`\x1b[35m════════ Step ${step}/${totalSteps}: ${msg} ════════\x1b[0m`);
}

function run(cmd, args, cwd, { optional = false } = {}) {
  log(`$ ${cmd} ${args.join(' ')}  (in ${path.relative(root, cwd) || '.'})`);
  const res = spawnSync(cmd, args, { stdio: 'inherit', cwd, shell: false });
  if (res.error && res.error.code === 'ENOENT') {
    fail(`"${cmd}" is not installed or not on PATH.`);
  }
  if (res.status !== 0) {
    if (optional) {
      log('(step failed but is optional — continuing)');
      return;
    }
    fail(`command failed with exit code ${res.status}. See output above.`);
  }
}

function fail(msg) {
  console.error('');
  console.error(`\x1b[31m✗ ${msg}\x1b[0m`);
  process.exit(1);
}

function platformTarget() {
  if (IS_WIN) return ['--win'];
  if (os.platform() === 'darwin') return ['--mac'];
  return ['--linux'];
}

function main() {
  console.log('');
  log('Building your Diorite installer — one command, one EXE at the end.');
  log(`Repo: ${root}`);

  // ---------- Step 1: sanity checks ----------
  banner('Checking tools');
  run('node', ['--version'], root);
  const npmCmd = IS_WIN ? 'npm.cmd' : 'npm';
  run(npmCmd, ['--version'], root);

  let py = null;
  for (const candidate of ['python', 'python3', 'py']) {
    const res = spawnSync(candidate, ['--version'], { stdio: 'ignore', shell: false });
    if (res.status === 0) { py = candidate; break; }
  }
  if (!py) {
    fail([
      'Python 3.11+ is required to freeze the backend into an exe.',
      'Install it from https://python.org and re-run this script.',
    ].join('\n'));
  }
  log(`Node ✓  npm ✓  Python ✓ (${py})`);

  // ---------- Step 2: freeze the backend into ONE exe ----------
  banner('Freezing backend into a standalone exe (no Python needed for users)');
  run(py, ['-m', 'pip', 'install', '-q', '-r', 'requirements.txt'], path.join(root, 'backend'));
  run(py, ['-m', 'pip', 'install', '-q', 'pyinstaller'], path.join(root, 'backend'));
  run(py, ['-m', 'PyInstaller', 'diorite-backend.spec', '--clean', '--noconfirm'], path.join(root, 'backend'));

  const backendExe = path.join(
    root, 'backend', 'dist', 'diorite-backend',
    IS_WIN ? 'diorite-backend.exe' : 'diorite-backend'
  );
  if (!fs.existsSync(backendExe)) {
    fail(`backend exe was not created at expected path:\n  ${backendExe}`);
  }
  log(`Backend exe ready: ${path.relative(root, backendExe)}`);

  // ---------- Step 3: build frontend ----------
  banner('Building frontend (React + Vite + Monaco)');
  run(npmCmd, ['install'], path.join(root, 'frontend'));
  run(npmCmd, ['run', 'build'], path.join(root, 'frontend'));

  // ---------- Step 4: build electron ----------
  banner('Building Electron shell');
  run(npmCmd, ['install'], path.join(root, 'electron'));
  run(npmCmd, ['run', 'build'], path.join(root, 'electron'));

  // ---------- Step 5: package the installer ----------
  banner('Packaging the installer');
  const npxCmd = IS_WIN ? 'npx.cmd' : 'npx';
  run(npxCmd, ['electron-builder', '--config', '../installer/electron-builder.yml', ...platformTarget()], path.join(root, 'electron'));

  // ---------- Done ----------
  const installerDir = path.join(root, 'dist', 'installer');
  console.log('');
  console.log('\x1b[32m════════════════████████████████════════════════════════\x1b[0m');
  if (fs.existsSync(installerDir)) {
    const artifacts = fs.readdirSync(installerDir).filter(f =>
      f.endsWith('.exe') || f.endsWith('.dmg') || f.endsWith('.AppImage') || f.endsWith('.zip'));
    if (artifacts.length) {
      log(`Done! Your installer is ready — share this ONE file:`);
      artifacts.forEach(f => console.log(`\x1b[32m  ✔ dist/installer/${f}\x1b[0m`));
      console.log('');
      log('To use Diorite: double-click it → desktop shortcut appears → open Diorite.');
      log('(No Python / Node / Java / anything else required on that machine.)');
      return;
    }
  }
  log('Build finished. Check dist/installer/ for artifacts.');
}

try {
  main();
} catch (err) {
  if (FAIL_FAST) throw err;
  fail(err.message || String(err));
}
