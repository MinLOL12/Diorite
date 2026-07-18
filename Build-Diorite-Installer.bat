@echo off
REM ================================================================
REM  Diorite - ONE double-click to build the installer EXE.
REM
REM  Output: dist\installer\Diorite-Setup-<version>-x64.exe
REM  Share that ONE file. Users double-click it and that is all.
REM ================================================================
cd /d %~dp0

title Building Diorite Installer...

where node >nul 2>nul
if errorlevel 1 (
  echo.
  echo  ERROR: Node.js is not installed.
  echo  Get it from https://nodejs.org (LTS), then double-click this file again.
  echo.
  pause
  exit /b 1
)

where python >nul 2>nul
if errorlevel 1 (
  echo.
  echo  ERROR: Python is not installed.
  echo  Get Python 3.11+ from https://python.org (tick "Add to PATH"),
  echo  then double-click this file again.
  echo.
  pause
  exit /b 1
)

node scripts\build-installer.js
if errorlevel 1 (
  echo.
  echo  Build failed - see messages above.
  pause
  exit /b 1
)

echo.
echo  ====================================================
echo   SUCCESS! Your installer EXE is in dist\installer\
echo   Double-click it on any PC to install and run Diorite.
echo  ====================================================
echo.
start "" "dist\installer"
pause
