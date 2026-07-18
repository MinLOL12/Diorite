@echo off
REM Kept for compatibility — everything now goes through ONE builder.
REM Prefer: double-click ..\Build-Diorite-Installer.bat  (repo root)
cd /d %~dp0\..
node scripts\build-installer.js
pause
