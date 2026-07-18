# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec — builds the standalone Diorite backend (one exe).
#
#   pip install pyinstaller
#   pyinstaller diorite-backend.spec --clean --noconfirm
#
# Output: backend/dist/diorite-backend/  (diorite-backend.exe + _internal/)
# The installer bundles this folder, so users never need Python installed.

from PyInstaller.utils.hooks import collect_submodules

# FastAPI/uvicorn and friends use lazy/dynamic imports — collect them all.
hiddenimports = (
    collect_submodules("uvicorn")
    + collect_submodules("websockets")
    + collect_submodules("watchdog")
    + collect_submodules("psutil")
    + [
        "multipart",          # python-multipart (FastAPI form parsing)
        "aiofiles",
        "httpx",
        "rich",
        "backend.app.main",   # in case Analysis is run from repo root
    ]
)

a = Analysis(
    ["run_backend.py"],
    pathex=["."],
    binaries=[],
    # Ship the built-in mod templates inside the exe bundle.
    datas=[("templates", "templates")],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["pytest", "tkinter", "PyQt5", "PyQt6", "PySide2", "PySide6"],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="diorite-backend",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,   # Electron hides the window via windowsHide; keeps logs
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="diorite-backend",
)
