# Diorite Installer

`electron-builder.yml` — config for the ONE-CLICK installer. You never run this
by hand; use one of these instead:

## Build the EXE (pick ONE)

|Way|How|Needs|
|---|---|---|
|**GitHub button** (easiest — nothing installed)|One-time: copy `workflows/build-installer.yml` (this folder) to `.github/workflows/` and push. Then Repo → Actions → *Build Installer* → Run → download `Diorite-Setup-Windows` artifact|nothing|
|**Double-click**|`Build-Diorite-Installer.bat` (repo root)|Node 20+, Python 3.11+|
|**Terminal**|`npm run make:exe`|Node 20+, Python 3.11+|

Output: `dist/installer/Diorite-Setup-<version>-x64.exe`

## What users do with the EXE

1. Double-click `Diorite-Setup-*.exe` — it installs itself, no wizard questions.
2. Double-click the new **Diorite** desktop shortcut — app opens. Done.

The backend ships frozen inside the app (PyInstaller), so end users need
**no Python, Node, JDK, or Gradle** installed. On a tag push (`v1.0.0`) the
workflow also publishes the EXE to **GitHub Releases**.
