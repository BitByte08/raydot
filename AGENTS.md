# Raydot — 정독실 출입 제어 시스템 모노레포

**Generated:** 2026-05-26 (Asia/Seoul)

## Overview

학교 정독실(독서실) 출입 제어 시스템. ESP32 기반 출입문 제어 장치(firmware) + Raspberry Pi 기반 키오스크(frontend) + 관리자 웹(admin-web) + 백엔드 서버(backend)로 구성된 IoT 시스템.

**런타임 환경:**
- `firmware`: ESP32-WROVER (lolin_d32_pro), PlatformIO + Arduino framework
- `frontend`: Raspberry Pi 4, kiosk 모드 웹 앱 (React/Vue + Electron)
- `admin-web`: Raspberry Pi 4, 관리자 웹 페이지 (React/Vue)
- `backend`: Raspberry Pi 4, Node.js/Python FastAPI + MQTT broker

## Structure

```
Raydot/
├── firmware/        # ESP32 출입문 제어 장치 (기존 Door.dot)
│   ├── src/         # FreeRTOS tasks + UART QR scanner + MQTT
│   ├── platformio.ini
│   └── docs/        # (stale design docs)
├── frontend/        # Vue 3 SPA (Raspberry Pi)
│   ├── kiosk/       # 학생용 키오스크 UI (Electron fullscreen)
│   │   └── PLAN.md  # auth, desk, check-in/out, board 기능
│   └── admin/       # 관리자 웹 페이지 (Nginx SPA)
│       └── PLAN.md  # user/room/door/qr/board 관리 기능
├── backend/         # 통합 백엔드 API + MQTT broker (Raspberry Pi)
│   └── PLAN.md      # REST API + MQTT topics + DB schema
└── AGENTS.md        # 모노레포 루트 가이드
```

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Raspberry Pi 4 (Backend)                           │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐   ┌─────────────────┐ │
│  │  MQTT Broker│   │  REST API   │   │   Database  │   │   Admin Web     │ │
│  │  (Mosquitto)│   │  (FastAPI)  │   │  (PostgreSQL│   │   (Nginx + Vue) │ │
│  └──────┬──────┘   └──────┬──────┘   └──────┬──────┘   └─────────────────┘ │
│         │                 │                 │                               │
└─────────│─────────────────│─────────────────│───────────────────────────────┘
          │                 │                 │
          │ MQTT            │ HTTP            │
          │                 │                 │
┌─────────│─────────────────│─────────────────│───────────────────────────────┐
│         │                 │                 │                               │
│  ┌──────▼──────┐   ┌──────▼──────┐   ┌──────▼──────┐                       │
│  │   ESP32     │   │  Kiosk UI   │   │  Admin Web  │                       │
│  │  (firmware) │   │ (frontend)  │   │  (browser)  │                       │
│  │             │   │             │   │             │                       │
│  │ - QR scan   │   │ - 학생 로그인│   │ - 사용자 관리│                       │
│  │ - MQTT pub  │   │ - 좌석 선택 │   │ - 정독실 관리│                       │
│  │ - Relay     │   │ - QR 발급   │   │ - 출입문 상태│                       │
│  └──────┬──────┘   └──────┬──────┘   └──────┬──────┘                       │
│         │                 │                 │                               │
└─────────│─────────────────│─────────────────│───────────────────────────────┘
          │                 │
          │ MQTT            │ HTTP
          │                 │
     ┌────▼────┐        ┌────▼────┐
     │ 출입문  │        │ RFID/   │
     │ (Relay) │        │ Barcode │
     └───────┬─┘        │ Scanner │
             │          └───────┬─┘
             │                  │
        ┌────▼────┐             │
        │ EM Lock │             │
        └───────┬─┘             │
                │               │
            ┌───▼───┐           │
            │  Door │           │
            └───────┘           │
                                │
                     학생증 RFID/바코드 입력
```

## MQTT Topic Tree

```
door/{roomCode}/
├── status              # FW → Backend: 연결 상태 + 잠금 상태 (retained)
├── event               # FW → Backend: door_open, door_close
├── auth/request        # FW → Backend: QR 인증 요청
├── auth/response       # Backend → FW: 인증 결과 (success, user_name, duration)
├── command             # Backend → FW: open, close 명령

kiosk/{roomCode}/
├── status              # Frontend → Backend: 연결 상태
├── seat/state          # Frontend ↔ Backend: 좌석 상태 변경
├── check-in            # Frontend → Backend: 입실 요청
├── check-out           # Frontend → Backend: 퇴실 요청
├── qr/issue            # Backend → Frontend: QR 발급 결과

admin/{roomCode}/
├── user/create         # Admin → Backend: 사용자 생성
├── user/blacklist      # Admin → Backend: 블랙리스트 등록
├── room/desk/create    # Admin → Backend: 좌석 생성
├── door/state          # Backend → Admin: 출입문 상태 (실시간)
├── board/notify        # Admin → Backend: 공지사항 등록
```

## Cross-Repo Conventions

- **API Protocol**: REST (JSON) + MQTT (JSON payloads)
- **Auth**: 학생증 RFID/바코드 → 4자리 PIN, 관리자 → 학교 이메일 + 비밀번호
- **QR Format**: `USER:{userId}:{seatId}:{timestamp}:{signature}` (backend 서명)
- **Room Code**: 정독실 식별 코드 (예: `R001`, `READING-A`)
- **Timestamps**: ISO 8601 (UTC)
- **Language**: 한국어 UI, 영어 코드 comments

## Commands

각 서비스 디렉터리에서 별도 빌드/실행. 루트에는 통합 스크립트 없음 (나중에 docker-compose로 통합 가능).

```bash
# Firmware
cd firmware && pio run --target upload

# Backend (Python FastAPI)
cd backend && pip install -r requirements.txt && uvicorn main:app --host 0.0.0.0 --port 8000

# Frontend (Electron kiosk)
cd frontend && npm install && npm run build && electron .

# Admin-web (Vue SPA)
cd admin-web && npm install && npm run build && nginx -s reload
```

## Where to Look

| 작업 | 위치 |
|------|------|
| ESP32 출입문 제어 로직 | [firmware/src/tasks/StateManagerTask.h](../firmware/src/tasks/StateManagerTask.h) |
| QR 스캐너 UART 연결 | [firmware/src/scanner/QRScanner.cpp](../firmware/src/scanner/QRScanner.cpp) |
| MQTT topic/payload 정의 | [backend/PLAN.md](backend/PLAN.md) MQTT Topics 섹션 |
| 학생 로그인 플로우 | [frontend/PLAN.md](frontend/PLAN.md) auth/login |
| 관리자 기능 전체 | [admin-web/PLAN.md](admin-web/PLAN.md) |
| GPIO 핀 제약 | [firmware/src/config/pins.h](../firmware/src/config/pins.h) |

## Next Steps

1. `backend/PLAN.md` → DB schema + REST API endpoints 설계 완료 후 구현
2. `frontend/PLAN.md` → 와이어프레임 받은 후 UI 컴포넌트 구현
3. `admin-web/PLAN.md` → 와이어프레임 받은 후 관리자 페이지 구현
4. MQTT broker 설치 (Mosquitto) → backend에서 실행
5. Raspberry Pi 4 세팅 → frontend + admin-web + backend 배포

## Notes

- firmware는 이미 구현됨 (Door.dot). MQTT 연동 테스트 필요.
- frontend, backend, admin-web은 새 프로젝트 — PLAN.md에서 설계만 완료, 구현은 나중에.
- 와이어프레임은 MCP로 제공 예정 — 받은 후 각 PLAN.md에 맵핑.