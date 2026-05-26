#!/bin/bash
set -e

RAYDOT_HOME="/home/pi/raydot"

echo "=== Raydot Installer for Raspberry Pi ==="

# Install system dependencies
echo "[1/6] Installing system packages..."
sudo apt-get update -qq
sudo apt-get install -y -qq python3 python3-pip nodejs npm nginx mosquitto mosquitto-clients

# Setup Mosquitto
echo "[2/6] Configuring MQTT broker..."
sudo cp "$RAYDOT_HOME/backend/mosquitto.conf" /etc/mosquitto/conf.d/raydot.conf
if ! sudo grep -q raydot /etc/mosquitto/passwd 2>/dev/null; then
    sudo mosquitto_passwd -b -c /etc/mosquitto/passwd raydot raydot
fi
sudo systemctl enable mosquitto
sudo systemctl restart mosquitto

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
User=pi
WorkingDirectory=$RAYDOT_HOME/backend
ExecStart=/usr/bin/python3 -m uvicorn main:app --host 0.0.0.0 --port 8000
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
sudo nginx -t && sudo systemctl restart nginx

# Setup kiosk autostart
echo "[6/6] Configuring kiosk autostart..."
mkdir -p /home/pi/.config/lxsession/LXDE-pi
cat > /home/pi/.config/lxsession/LXDE-pi/autostart << EOF
@xset s off
@xset -dpms
@xset s noblank
@cd $RAYDOT_HOME/frontend/kiosk && npx electron .
EOF

echo ""
echo "=== Installation complete ==="
echo "Backend API: http://$(hostname -I | awk '{print $1}'):8000"
echo "Admin panel: http://$(hostname -I | awk '{print $1}')"
echo "Kiosk: will auto-start on next boot"
echo ""
echo "To start kiosk now: cd $RAYDOT_HOME/frontend/kiosk && npx electron ."
