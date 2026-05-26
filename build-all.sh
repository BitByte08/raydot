#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=== Raydot Build Script ==="

# Backend
echo "[1/4] Installing backend dependencies..."
cd "$SCRIPT_DIR/backend"
python3 -m venv venv 2>/dev/null || true
source venv/bin/activate
pip install -r requirements.txt

echo "[2/4] Initializing database..."
python3 init_db.py

# Kiosk
echo "[3/4] Building kiosk frontend..."
cd "$SCRIPT_DIR/frontend/kiosk"
npm install --legacy-peer-deps 2>/dev/null || npm install
npm run build

# Admin
echo "[4/4] Building admin frontend..."
cd "$SCRIPT_DIR/frontend/admin"
npm install --legacy-peer-deps 2>/dev/null || npm install
npm run build

echo ""
echo "=== Build complete ==="
echo "Next steps:"
echo "  1. Copy backend/.env.example to backend/.env and edit"
echo "  2. sudo cp frontend/admin/nginx.conf /etc/nginx/sites-available/raydot"
echo "  3. sudo ln -sf /etc/nginx/sites-available/raydot /etc/nginx/sites-enabled/"
echo "  4. sudo systemctl restart nginx"
echo "  5. sudo systemctl start raydot-backend"
echo "  6. Run kiosk: cd frontend/kiosk && npx electron ."
