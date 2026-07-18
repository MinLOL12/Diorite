#!/usr/bin/env node
const { spawn } = require('child_process');
const path = require('path');
const root = path.join(__dirname, '..');

function start(name, cmd, args, cwd, color) {
  const proc = spawn(cmd, args, { cwd, stdio: 'inherit', shell: true });
  proc.on('exit', code => console.log(`[${name}] exited ${code}`));
  return proc;
}

console.log('Starting Diorite dev servers...');
console.log('- Backend  http://127.0.0.1:7331 (FastAPI)');
console.log('- Frontend http://127.0.0.1:7332 (Vite)');
console.log('- Logs stream via WebSockets: ws://127.0.0.1:7331/ws/{logs,build,process}/{projectId}');
console.log('Press Ctrl+C to stop.');

const backend = start('backend', 'python', ['-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', '7331', '--reload'], path.join(root, 'backend'), '32');
const frontend = start('frontend', 'npm', ['run', 'dev'], path.join(root, 'frontend'), '36');

process.on('SIGINT', () => {
  backend.kill();
  frontend.kill();
  process.exit(0);
});
