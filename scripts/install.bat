@echo off
REM Diorite Windows Development Installer / Portable Builder
echo === Diorite Installer ===
echo Building frontend, backend, electron...

cd /d %~dp0\..

echo [1/4] Checking Python...
python --version || goto :error

echo [2/4] Installing backend deps...
cd backend
pip install -r requirements.txt
cd ..

echo [3/4] Building frontend...
cd frontend
call npm install
call npm run build
cd ..

echo [4/4] Building electron...
cd electron
call npm install
call npm run build
cd ..

echo Creating portable package...
mkdir dist\diorite-portable 2>nul
xcopy /E /I /Y frontend\dist dist\diorite-portable\frontend\dist
xcopy /E /I /Y backend dist\diorite-portable\backend
xcopy /E /I /Y electron\dist dist\diorite-portable\electron\dist
xcopy /E /I /Y assets dist\diorite-portable\assets
copy package.json dist\diorite-portable\

echo Creating run.bat...
(
echo @echo off
echo echo Starting Diorite...
echo cd /d %%~dp0
echo start http://127.0.0.1:7332
echo cd backend
echo python -m uvicorn app.main:app --host 127.0.0.1 --port 7331
) > dist\diorite-portable\run.bat

echo Done! Portable at dist\diorite-portable\
echo To create full EXE installer, run:
echo   npx electron-builder --config installer/electron-builder.yml --win --x64
goto :eof

:error
echo Python not found, please install Python 3.11+
exit /b 1
