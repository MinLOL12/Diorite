#!/bin/bash
# ══════════════════════════════════════════════════════════════════
#  Diorite - ONE command to build the installer.
#
#  Output: dist/installer/  (AppImage on Linux, DMG on macOS)
#  Note: the Windows .exe installer requires a Windows build agent —
#        use Build-Diorite-Installer.bat there, or GitHub Actions
#        (.github/workflows/build-installer.yml) and just download the
#        ready-made EXE.
# ══════════════════════════════════════════════════════════════════
set -e
cd "$(dirname "$0")"
node scripts/build-installer.js
