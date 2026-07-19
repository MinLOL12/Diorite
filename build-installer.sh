#!/bin/bash
# ══════════════════════════════════════════════════════════════════
#  Diorite - ONE command to build the installer.
#
#  Output: dist/installer/  (AppImage on Linux, DMG on macOS,
#          EXE on Windows if you run the .bat or this on Windows)
#
#  NO-INSTALL method (nothing needed locally):
#    GitHub repo → Actions → Build Installer → Run workflow
#    → download Diorite-Setup-Windows artifact.
#    Workflow file is at .github/workflows/build-installer.yml
#    (mirror at installer/workflows/build-installer.yml)
#
#  LOCAL method (this script):
#    ./build-installer.sh    (Linux/macOS)
#    Build-Diorite-Installer.bat  (Windows double-click)
#    npm run make:exe        (any OS terminal)
# ══════════════════════════════════════════════════════════════════
set -e
cd "$(dirname "$0")"
node scripts/build-installer.js
