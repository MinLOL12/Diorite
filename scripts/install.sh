#!/bin/bash
set -e
echo "=== Diorite Installer (Linux/macOS) ==="
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "[1/4] Python check"
python3 --version

echo "[2/4] Backend deps"
pip3 install -q -r backend/requirements.txt --break-system-packages || pip3 install -q -r backend/requirements.txt

echo "[3/4] Frontend build"
cd frontend
npm install
npm run build
cd ..

echo "[4/4] Electron build"
cd electron
npm install
npm run build || true
cd ..

echo "Creating portable..."
mkdir -p dist/diorite-portable
cp -r frontend/dist dist/diorite-portable/frontend_dist
cp -r backend dist/diorite-portable/backend
cp -r electron/dist dist/diorite-portable/electron_dist
cp -r assets dist/diorite-portable/

cat > dist/diorite-portable/run.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
echo "Starting Diorite backend at http://127.0.0.1:7331"
echo "Frontend at http://127.0.0.1:7332 - open browser"
cd backend
python3 -m uvicorn app.main:app --host 127.0.0.1 --port 7331 &
BACKEND_PID=$!
cd ../frontend
npm run dev &
FRONTEND_PID=$!
wait
EOF
chmod +x dist/diorite-portable/run.sh

echo "Done! Portable at dist/diorite-portable/"
echo "To build EXE installer (on Windows): npx electron-builder --config installer/electron-builder.yml --win --x64"
