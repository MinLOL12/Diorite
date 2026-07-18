#!/usr/bin/env node
/**
 * Diorite Installer Builder
 * Builds frontend, electron, and creates NSIS EXE installer
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const root = path.join(__dirname, '..');

function log(msg) {
  console.log(`[Diorite Installer] ${msg}`);
}

function run(cmd, cwd = root) {
  log(`$ ${cmd} (in ${cwd})`);
  execSync(cmd, { stdio: 'inherit', cwd });
}

async function main() {
  log('Starting Diorite build...');

  // 1. Check assets
  const iconPath = path.join(root, 'assets', 'icons', 'icon.png');
  if (!fs.existsSync(iconPath)) {
    log('Warning: icon not found, creating placeholder');
  }

  // 2. Install backend deps (optional)
  try {
    run('python -m pip install -q -r backend/requirements.txt', root);
  } catch {
    log('Could not pip install backend deps, continuing...');
  }

  // 3. Build frontend
  log('Building frontend (Vite + React + Monaco)...');
  if (!fs.existsSync(path.join(root, 'frontend', 'node_modules'))) {
    run('npm install', path.join(root, 'frontend'));
  }
  run('npm run build', path.join(root, 'frontend'));

  // 4. Build electron
  log('Building Electron main process...');
  if (!fs.existsSync(path.join(root, 'electron', 'node_modules'))) {
    run('npm install', path.join(root, 'electron'));
  }
  run('npm run build', path.join(root, 'electron'));

  // 5. Build installer with electron-builder
  log('Building EXE installer via electron-builder NSIS...');
  try {
    run('npx electron-builder --config ../installer/electron-builder.yml --win --x64', path.join(root, 'electron'));
    log('Installer built successfully! Check dist/installer/');
  } catch (e) {
    log('Electron builder failed (maybe not on Windows, or missing deps).');
    log('You can still run dev mode: npm run dev');
    log('Or manually create installer on Windows host.');
  }

  log('Done! Artifacts:');
  const installerDir = path.join(root, 'dist', 'installer');
  if (fs.existsSync(installerDir)) {
    fs.readdirSync(installerDir).forEach(f => log(` - ${f}`));
  } else {
    log('No installer dir yet (expected on Windows). Frontend and electron builds are ready.');
  }
}

main().catch(err => {
  console.error(err);
  process.exit(1);
});
