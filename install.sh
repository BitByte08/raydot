#!/bin/bash
set -e

# Auto-detect repo root — works regardless of clone path or username
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
RAYDOT_HOME="$SCRIPT_DIR"
CURRENT_USER="$(whoami)"

echo "=== Raydot Installer for Raspberry Pi ==="
echo "Repo: $RAYDOT_HOME"
echo "User: $CURRENT_USER"
echo ""

# Install system dependencies
echo "[1/6] Installing system packages..."
sudo apt-get update -qq
sudo apt-get install -y -qq python3 python3-pip python3-venv nodejs npm nginx mosquitto mosquitto-clients fonts-noto-cjk onboard

# Setup Mosquitto
echo "[2/6] Configuring MQTT broker..."
sudo cp "$RAYDOT_HOME/backend/mosquitto.conf" /etc/mosquitto/conf.d/raydot.conf
# Disable default listener to avoid port conflict
sudo sed -i 's/^listener /#listener /' /etc/mosquitto/mosquitto.conf 2>/dev/null || true
sudo sed -i 's/^port /#port /' /etc/mosquitto/mosquitto.conf 2>/dev/null || true
sudo systemctl enable mosquitto
sudo systemctl restart mosquitto || {
    echo "Mosquitto restart failed, checking logs..."
    sudo journalctl -xeu mosquitto --no-pager -n 10
}

# Build
echo "[3/6] Building all components..."
bash "$RAYDOT_HOME/build-all.sh"

# Setup backend systemd service
echo "[4/6] Installing backend service..."
sudo tee /etc/systemd/system/raydot-backend.service > /dev/null << EOF
[Unit]
Description=Raydot Backend API
After=network.target mosquitto.service

[Service]
Type=simple
User=$CURRENT_USER
WorkingDirectory=$RAYDOT_HOME/backend
ExecStart=$RAYDOT_HOME/backend/venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable raydot-backend
sudo systemctl start raydot-backend

# Setup Nginx
echo "[5/6] Configuring Nginx..."
sudo cp "$RAYDOT_HOME/frontend/admin/nginx.conf" /etc/nginx/sites-available/raydot
sudo rm -f /etc/nginx/sites-enabled/default
sudo ln -sf /etc/nginx/sites-available/raydot /etc/nginx/sites-enabled/
sudo sed -i "s|/home/pi/raydot|$RAYDOT_HOME|g" /etc/nginx/sites-available/raydot
sudo nginx -t && sudo systemctl restart nginx

# Setup kiosk autostart
echo "[6/6] Configuring kiosk autostart..."

# Method 1: XDG autostart (works on LXDE, XFCE, GNOME, Wayfire via lxqt-panel)
mkdir -p "$HOME/.config/autostart"
cat > "$HOME/.config/autostart/raydot-kiosk.desktop" << EOF
[Desktop Entry]
Type=Application
Name=Raydot Kiosk
Exec=bash -c "onboard & sleep 1; cd $RAYDOT_HOME/frontend/kiosk && npx electron ."
X-GNOME-Autostart-enabled=true
EOF

# Method 2: Wayfire autostart (RPi OS Bookworm default)
if [ -f "$HOME/.config/wayfire.ini" ]; then
    if ! grep -q "raydot" "$HOME/.config/wayfire.ini" 2>/dev/null; then
        echo "[autostart]" >> "$HOME/.config/wayfire.ini"
        echo "raydot = bash -c 'onboard & sleep 1; cd $RAYDOT_HOME/frontend/kiosk && npx electron .'" >> "$HOME/.config/wayfire.ini"
    fi
fi

# Method 3: LXDE-pi (older RPi OS)
mkdir -p "$HOME/.config/lxsession/LXDE-pi"
cat > "$HOME/.config/lxsession/LXDE-pi/autostart" << EOF
@xset s off
@xset -dpms
@xset s noblank
@onboard &
@cd $RAYDOT_HOME/frontend/kiosk && npx electron .
EOF

echo "Kiosk will auto-start on next GUI login."

echo ""
echo "=== Installation complete ==="
echo "Backend API: http://$(hostname -I | awk '{print $1}'):8000"
echo "Admin panel: http://$(hostname -I | awk '{print $1}')"
echo "Kiosk: will auto-start on next boot"
echo ""
echo "To start kiosk now: cd $RAYDOT_HOME/frontend/kiosk && npx electron ."
