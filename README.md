# Raydot — 정독실 출입 제어 시스템

학교 정독실(독서실) 출입 제어 IoT 시스템.

- **Backend**: Python FastAPI + SQLite + MQTT (Mosquitto)
- **Kiosk**: Vue 3 + Electron (Raspberry Pi 7" 터치 디스플레이, 800x480)
- **Admin**: Vue 3 SPA (Nginx)
- **Firmware**: ESP32-WROVER + PlatformIO (출입문 제어)

## Quick Start (Raspberry Pi)

```bash
git clone https://github.com/BitByte08/raydot.git /home/pi/raydot
cd /home/pi/raydot
bash install.sh
```

## Local Dev

```bash
# Backend
cd backend && pip install -r requirements.txt && uvicorn main:app --port 8000

# Mosquitto (MQTT broker)
sudo pacman -S mosquitto  # Arch
# or: sudo apt install mosquitto  # Debian/Ubuntu

# Kiosk
cd frontend/kiosk && npm install && npm run dev

# Admin
cd frontend/admin && npm install && npm run dev
```

## API

| Method | Path | Auth |
|--------|------|------|
| `POST` | `/api/auth/login` | — |
| `POST` | `/api/admin/login` | — |
| `GET` | `/api/rooms` | — |
| `GET` | `/api/room/{code}/seats` | — |
| `POST` | `/api/room/{code}/check-in` | JWT |
| `POST` | `/api/room/{code}/check-out` | JWT |
| `GET` | `/api/admin/rooms` | Admin JWT |
| `POST` | `/api/admin/user/create` | Admin JWT |
| ... | 30+ endpoints total | |

## MQTT Topics

```
door/{roomCode}/status         # FW → Backend (retained)
door/{roomCode}/event          # FW → Backend
door/{roomCode}/auth/request   # FW → Backend (QR auth)
door/{roomCode}/auth/response  # Backend → FW
door/{roomCode}/command        # Backend → FW (open/close)

kiosk/{roomCode}/status        # Kiosk → Backend
kiosk/{roomCode}/seat/state    # Kiosk ↔ Backend (real-time)
```

## Architecture

```
ESP32 (firmware) ──MQTT──→ Raspberry Pi (backend + mosquitto)
                               ├── FastAPI REST API
                               ├── SQLite DB
                               ├── Admin Web (Nginx + Vue3)
                               └── MQTT ←→ Kiosk (Electron + Vue3)
```

## Deploy

```bash
# On Raspberry Pi:
git pull origin main
bash install.sh
# → Installs deps, builds all, configures systemd + nginx
```
