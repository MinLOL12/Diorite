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
 * The GitHub Actions workflow at .github/workflows/build-installer.yml does
 * the same thing in the cloud, so you don't need ANYTHING installed locally:
 * just go to Actions → Build Installer → Run workflow → download artifact.
 *
 * Options:
 *   --fail-fast   stop immediately on any error
 */
const { spawnSync } = require('child_process');
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
    fail(`"${cmd}" is not installed or not on PATH. Make sure it is installed and try again.`);
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
  console.error('');
  console.error('If you just want an EXE without installing anything locally:');
  console.error('  GitHub → your repo → Actions → Build Installer → Run workflow → download artifact');
  console.error('The workflow file is at .github/workflows/build-installer.yml (and mirrored at installer/workflows/build-installer.yml)');
  process.exit(1);
}
function platformTarget() {
  if (IS_WIN) return ['--win'];
  if (os.platform() === 'darwin') return ['--mac'];
  return ['--linux'];
}

function ensureDir(p) {
  if (!fs.existsSync(p)) fs.mkdirSync(p, { recursive: true });
}

function main() {
  console.log('');
  log('Building your Diorite installer — one command, one EXE at the end.');
  log(`Repo: ${root}`);
  log(`Docs: .github/workflows/build-installer.yml is the cloud (no-install) build — it already exists, no copying needed!`);
  log(`      Mirror copy lives at installer/workflows/build-installer.yml`);

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
      'OR: use the no-install method: GitHub → Actions → Build Installer → Run workflow',
    ].join('\n'));
  }
  log(`Node ✓  npm ✓  Python ✓ (${py})`);

  // Verify required files exist — this was the #1 confusion before
  const requiredFiles = [
    'backend/requirements.txt',
    'backend/diorite-backend.spec',
    'backend/run_backend.py',
    'frontend/package.json',
    'electron/package.json',
    'electron/src/main.ts',
    'installer/electron-builder.yml',
    '.github/workflows/build-installer.yml',
  ];
  const missing = requiredFiles.filter(f => !fs.existsSync(path.join(root, f)));
  if (missing.length) {
    fail(`Some required files are missing (did you clone the full repo?):\n  - ${missing.join('\n  - ')}\nMake sure you are in the repo root and all files are present.`);
  }

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
    fail(`backend exe was not created at expected path:\n  ${backendExe}\nCheck PyInstaller output above.`);
  }
  log(`Backend exe ready: ${path.relative(root, backendExe)}`);

  // ---------- Step 3: build frontend ----------
  banner('Building frontend (React + Vite + Monaco)');
  run(npmCmd, ['install'], path.join(root, 'frontend'));
  run(npmCmd, ['run', 'build'], path.join(root, 'frontend'));

  const frontendDist = path.join(root, 'frontend', 'dist', 'index.html');
  if (!fs.existsSync(frontendDist)) {
    fail(`Frontend did not build — expected ${path.relative(root, frontendDist)} missing`);
  }

  // ---------- Step 4: build electron ----------
  banner('Building Electron shell');
  run(npmCmd, ['install'], path.join(root, 'electron'));
  run(npmCmd, ['run', 'build'], path.join(root, 'electron'));

  const electronDist = path.join(root, 'electron', 'dist', 'main.js');
  if (!fs.existsSync(electronDist)) {
    fail(`Electron shell did not build — expected ${path.relative(root, electronDist)} missing`);
  }

  // ---------- Step 5: package the installer ----------
  banner('Packaging the installer');
  const npxCmd = IS_WIN ? 'npx.cmd' : 'npx';
  // Run from electron/ dir where its package.json lives, using config from installer/
  run(npxCmd, ['electron-builder', '--config', '../installer/electron-builder.yml', ...platformTarget()], path.join(root, 'electron'));

  // ---------- Done ----------
  const installerDir = path.join(root, 'dist', 'installer');
  console.log('');
  console.log('\x1b[32m════════════════════════════════════════════════════════\x1b[0m');
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
  log('Build finished but no EXE/DMG/AppImage found. Check dist/installer/ for artifacts and logs above.');
}

try {
  main();
} catch (err) {
  if (FAIL_FAST) throw err;
  fail(err.message || String(err));
}
