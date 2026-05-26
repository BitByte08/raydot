#!/bin/bash
set -e

echo "=== Raydot Build Script ==="

# Backend
echo "[1/4] Installing backend dependencies..."
cd "$(dirname "$0")/../backend"
pip3 install -r requirements.txt 2>/dev/null || pip install -r requirements.txt

echo "[2/4] Initializing database..."
python3 init_db.py

# Kiosk
echo "[3/4] Building kiosk frontend..."
cd "$(dirname "$0")/../frontend/kiosk"
npm install --legacy-peer-deps 2>/dev/null || npm install
npm run build

# Admin
echo "[4/4] Building admin frontend..."
cd "$(dirname "$0")/../frontend/admin"
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
