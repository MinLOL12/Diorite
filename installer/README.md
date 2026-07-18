# Diorite Installer

This folder contains configuration for building the Diorite EXE installer (NSIS).

## Building EXE on Windows

Prerequisites:
- Node 20+
- Python 3.11+
- Windows 10/11 (for NSIS)

Steps:

```bat
:: From repo root
npm install
npm run build:frontend
cd electron
npm install
npm run build
cd ..
npx electron-builder --config installer/electron-builder.yml --win --x64
```

Output:
```
dist/installer/Diorite-Setup-0.1.0-x64.exe
```

Run the EXE:
- Choose installation directory (default %LOCALAPPDATA%\Programs\Diorite)
- Creates desktop shortcut "Diorite IDE"
- Creates start menu shortcut
- Creates %APPDATA%\Diorite\ cache structure for Java, Gradle, MC, mappings, loaders
- Launch from shortcut — backend starts automatically on 127.0.0.1:7331, frontend embedded.

## One-Click Dev Installer

For quick local testing without full NSIS:

```bat
scripts\install.bat
```

This script:
1. Installs python deps
2. Builds frontend
3. Builds electron
4. Creates a portable folder dist/diorite-portable with run.bat

## What installer does

- Bundles backend (FastAPI) + frontend (React+Vite+Monaco) + Electron wrapper
- No JDK/Gradle needed — backend downloads to cache on first project creation
- Second Fabric 1.21.x project instant due to cache reuse
- Auto-updates disabled for now, but structure ready

## Icons

- Source: assets/icons/icon.png (generated, diorite texture D with emerald glow)
- Converted to .ico for NSIS via electron-builder (or copy png to ico placeholder on Linux)
- logo.svg vector version for web

## CI

On GitHub Actions Windows runner, add step:

```yaml
- run: npm run build:installer
- uses: actions/upload-artifact@v4
  with:
    name: Diorite-Setup
    path: dist/installer/*.exe
```
