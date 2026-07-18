import { app, BrowserWindow, dialog, shell, ipcMain } from 'electron';
import path from 'path';
import { spawn, ChildProcess } from 'child_process';
import fs from 'fs';
import os from 'os';

let mainWindow: BrowserWindow | null = null;
let backendProcess: ChildProcess | null = null;

const BACKEND_PORT = process.env.DIORITE_PORT || '7331';
const FRONTEND_PORT = process.env.DIORITE_FRONTEND_PORT || '7332';
const IS_DEV = !app.isPackaged;

function getBackendPath(): string {
  if (IS_DEV) {
    // In dev, we expect backend running separately via python
    return '';
  }
  // In production, backend bundled inside resources/backend
  // @ts-ignore - resourcesPath exists at runtime
  return path.join((process as any).resourcesPath, 'backend');
}

function getFrontendPath(): string {
  if (IS_DEV) {
    return `http://127.0.0.1:${FRONTEND_PORT}`;
  }
  // @ts-ignore
  return path.join((process as any).resourcesPath, 'frontend', 'dist', 'index.html');
}

function findBundledBackend(backendRoot: string): string | null {
  // Frozen single-exe backend produced by PyInstaller — zero-setup for users.
  const exeName = process.platform === 'win32' ? 'diorite-backend.exe' : 'diorite-backend';
  const candidates = [
    path.join(backendRoot, exeName),                  // resources/backend/diorite-backend(.exe)
    path.join(backendRoot, 'diorite-backend', exeName) // nested folder variant
  ];
  for (const candidate of candidates) {
    if (fs.existsSync(candidate)) return candidate;
  }
  return null;
}

function startBackend(): ChildProcess | null {
  if (IS_DEV) {
    console.log('[Diorite] Dev mode: expecting backend at http://127.0.0.1:' + BACKEND_PORT);
    return null;
  }

  const backendRoot = getBackendPath();
  let cmd: string;
  let args: string[];

  const bundledExe = findBundledBackend(backendRoot);
  if (bundledExe) {
    // Normal case: self-contained exe, nothing else needed on the machine.
    cmd = bundledExe;
    args = [];
    console.log(`[Diorite] Starting bundled backend: ${bundledExe}`);
  } else {
    // Fallback for source checkouts packaged without PyInstaller: system python.
    cmd = 'python';
    args = ['-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', BACKEND_PORT];
    console.log('[Diorite] Bundled backend not found, falling back to system python');
  }

  const proc = spawn(cmd, args, {
    cwd: backendRoot,
    env: {
      ...process.env,
      DIORITE_PORT: BACKEND_PORT,
      PYTHONUNBUFFERED: '1'
    },
    windowsHide: true, // no console window flashes on Windows
    stdio: ['ignore', 'pipe', 'pipe']
  });

  proc.stdout?.on('data', (data) => console.log(`[backend] ${data}`));
  proc.stderr?.on('data', (data) => console.error(`[backend] ${data}`));
  proc.on('exit', (code) => console.log(`[backend] exited with ${code}`));

  return proc;
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 1100,
    minHeight: 700,
    backgroundColor: '#0e0e0f',
    titleBarStyle: process.platform === 'darwin' ? 'hiddenInset' : 'default',
    title: 'Diorite - Minecraft IDE',
    icon: path.join(__dirname, '..', '..', 'assets', 'icons', 'icon.png'),
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      nodeIntegration: false,
      contextIsolation: true,
      webSecurity: !IS_DEV
    }
  });

  if (IS_DEV) {
    mainWindow.loadURL(`http://127.0.0.1:${FRONTEND_PORT}`);
    // mainWindow.webContents.openDevTools();
  } else {
    const frontendPath = getFrontendPath();
    if (frontendPath.startsWith('http')) {
      mainWindow.loadURL(frontendPath);
    } else {
      mainWindow.loadFile(frontendPath);
    }
  }

  mainWindow.webContents.setWindowOpenHandler(({ url }: { url: string }) => {
    shell.openExternal(url);
    return { action: 'deny' };
  });

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

app.whenReady().then(() => {
  backendProcess = startBackend();

  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    if (backendProcess) {
      backendProcess.kill();
    }
    app.quit();
  }
});

app.on('before-quit', () => {
  if (backendProcess) {
    backendProcess.kill();
  }
});

// IPC handlers
ipcMain.handle('get-app-version', () => app.getVersion());
ipcMain.handle('get-paths', () => ({
  userData: app.getPath('userData'),
  home: os.homedir(),
  backendPort: BACKEND_PORT,
  frontendPort: FRONTEND_PORT
}));
ipcMain.handle('show-item-in-folder', async (_: any, fullPath: string) => {
  shell.showItemInFolder(fullPath);
});
