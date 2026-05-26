# Backend — PLAN

통합 백엔드 서버. Raspberry Pi 4에서 Python FastAPI 또는 Node.js로 실행. MQTT broker + REST API + DB.

## Platform

- **Runtime**: Raspberry Pi 4, Python 3.10+ or Node.js 18+
- **Framework**: FastAPI (Python) or Express (Node.js)
- **MQTT Broker**: Mosquitto
- **Database**: PostgreSQL or SQLite (lightweight)
- **Auth**: JWT for admin, PIN for students

## API Endpoints

### Auth (학생)

```
POST /api/auth/login
  Body: { student_id: string, pin: string }
  Response: { success, user: User, blacklist: bool, token: string }
  Notes: PIN 4-digit, blacklist 확인 후 제한 안내

POST /api/auth/password/initial
  Body: { student_id: string, pin: string }
  Notes: 최초 PIN 설정, password_set=false → 설정 필요

POST /api/auth/password/find
  Body: { student_id: string }
  Notes: 등록된 email로 재설정 URL 발송
```

### Auth (관리자)

```
POST /api/admin/sign-up
  Body: { code: string, email: string, password: string }
  Notes: 고유 식별코드 + 학교 이메일 필수

POST /api/admin/verify-email
  Body: { token: string }
  Notes: 이메일 인증 완료

POST /api/admin/login
  Body: { email, password }
  Response: { token, admin: { id, name, role } }
```

### User

```
GET /api/user/{student_id}
  Response: User

POST /api/user/{student_id}/password/reset
  Body: { current_pin, new_pin }

GET /api/user/{student_id}/logs?range=30d
  Response: [{ date, check_in_time, check_out_time, seat_id, seat_number }]

POST /api/admin/user/create
  Body: { email, student_id, name, pin?: string }
  Notes: 관리자용 사용자 생성

GET /api/admin/users?grade={grade}
  Response: [User]

GET /api/admin/user/{student_id}/logs
  Response: logs (관리자용 전체 기록)

POST /api/admin/user/{student_id}/blacklist
  Body: { duration: "1w"|"1m"|"permanent", reason: string }

DELETE /api/admin/user/{student_id}/blacklist
  Notes: 블랙리스트 해제
```

### Room

```
GET /api/room/{room_code}/seats
  Response: { seats: [{ id, number, status, user_id?, user_name? }] }
  Notes: status: "empty"|"occupied"|"disabled"

POST /api/room/{room_code}/check-in
  Body: { seat_id, user_id, pass_type: "daily"|"weekly"|"monthly" }
  Response: { success, qr_code, expires_at }
  Notes: QR 생성 + 이메일 발송

POST /api/room/{room_code}/check-out
  Body: { seat_id, user_id }

POST /api/room/{room_code}/seat/move
  Body: { from_seat_id, to_seat_id, user_id }

GET /api/admin/room/{room_code}/seat/{seat_id}
  Response: Seat detail

PUT /api/admin/room/{room_code}/seat/{seat_id}/disable
  Body: { disabled: bool }

GET /api/admin/room/{room_code}/seat/{seat_id}/logs
  Response: seat logs

POST /api/admin/room/create
  Body: { code, name, seats: [{ number, enabled }] }

PUT /api/admin/room/{room_code}/seats
  Body: { seats: [...] }
  Notes: 좌석 배치 수정

GET /api/admin/rooms
  Response: [Room]
```

### Kiosk

```
POST /api/admin/room/{room_code}/kiosk/register
  Body: { kiosk_id: string }
  Notes: 키오스크-정독실 연결

GET /api/admin/room/{room_code}/kiosk/status
  Response: { connected, last_ping }
```

### Door

```
POST /api/admin/room/{room_code}/door/register
  Body: { door_id: string }
  Notes: 출입문-정독실 연결

GET /api/admin/room/{room_code}/door/status
  Response: { connected, lock_state: "locked"|"unlocked" }

GET /api/admin/room/{room_code}/door/logs
  Response: [{ time, event: "open"|"close", user_id?, user_name? }]

POST /api/room/{room_code}/door/command
  Body: { command: "open"|"close", param?: duration_seconds }
  Notes: 관리자가 출입문 직접 제어
```

### QR

```
GET /api/qr/{qr_id}
  Response: { qr_image_url, valid_until, user_id, seat_id, used }

GET /api/admin/qr?status={used|unused}
  Response: [{ qr_id, created_at, user_id, seat_id, used, expires_at }]

POST /api/qr/verify
  Body: { qr_code: string }
  Response: { valid, user_id, seat_id, expires_at }
  Notes: firmware에서 호출 — QR 스캔 시 인증

POST /api/admin/qr/revoke/{qr_id}
  Notes: QR 사용 불가 처리 (퇴실 후)
```

### Board

```
GET /api/board/notify?room_code={room_code}
  Response: [{ id, title, content, created_at, author }]

POST /api/admin/board/notify
  Body: { title, content: markdown }

PUT /api/admin/board/notify/{id}
  Body: { title, content }

DELETE /api/admin/board/notify/{id}

GET /api/board/inquiry/{user_id}
  Response: [{ id, content, status, reply?, reply_at? }]

POST /api/board/inquiry
  Body: { user_id, content }

POST /api/admin/board/inquiry/{id}/reply
  Body: { reply: string }

DELETE /api/admin/board/inquiry/{id}
```

## MQTT Topics

### Firmware → Backend

```
Publish:
door/{roomCode}/status
  Payload: { connected: bool, lock_state: "locked"|"unlocked", ip: string }
  Retained: true

door/{roomCode}/event
  Payload: { type: "door_open"|"door_close", user_id?, timestamp }

door/{roomCode}/auth/request
  Payload: { qr_code: string, timestamp }

Subscribe:
door/{roomCode}/auth/response
  Payload: { success: bool, user_name?: string, duration?: int }

door/{roomCode}/command
  Payload: { command: "open"|"close", param?: int }
```

### Kiosk → Backend

```
Publish:
kiosk/{roomCode}/status
  Payload: { connected: bool, ip: string }
  Retained: true

kiosk/{roomCode}/check-in
  Payload: { seat_id, user_id, pass_type }

kiosk/{roomCode}/check-out
  Payload: { seat_id, user_id }

kiosk/{roomCode}/seat/state
  Payload: { seat_id, status: "empty"|"occupied", user_id? }

Subscribe:
kiosk/{roomCode}/seat/state
  Payload: { seat_id, status, user_id?, user_name? }
  Notes: 다른 kiosk에서 상태 변경 → 전파

kiosk/{roomCode}/qr/issue
  Payload: { qr_code, expires_at, user_id, seat_id }
```

### Admin → Backend

```
Subscribe:
door/{roomCode}/status
door/{roomCode}/event
kiosk/{roomCode}/status
kiosk/{roomCode}/seat/state

Publish:
door/{roomCode}/command (직접 제어)
```

## Database Schema

### Users

```sql
CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  student_id VARCHAR(20) UNIQUE NOT NULL,
  name VARCHAR(100) NOT NULL,
  email VARCHAR(100) UNIQUE NOT NULL,
  pin VARCHAR(4) DEFAULT NULL,
  password_set BOOLEAN DEFAULT false,
  blacklist BOOLEAN DEFAULT false,
  blacklist_until TIMESTAMP DEFAULT NULL,
  blacklist_reason TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);
```

### Admins

```sql
CREATE TABLE admins (
  id SERIAL PRIMARY KEY,
  email VARCHAR(100) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  name VARCHAR(100),
  role VARCHAR(20) DEFAULT 'staff',
  verified BOOLEAN DEFAULT false,
  created_at TIMESTAMP DEFAULT NOW()
);
```

### Rooms

```sql
CREATE TABLE rooms (
  id SERIAL PRIMARY KEY,
  code VARCHAR(20) UNIQUE NOT NULL,
  name VARCHAR(100),
  kiosk_id VARCHAR(50),
  door_id VARCHAR(50),
  created_at TIMESTAMP DEFAULT NOW()
);
```

### Seats

```sql
CREATE TABLE seats (
  id SERIAL PRIMARY KEY,
  room_id INT REFERENCES rooms(id),
  number VARCHAR(10) NOT NULL,
  disabled BOOLEAN DEFAULT false,
  UNIQUE(room_id, number)
);
```

### Seat Logs

```sql
CREATE TABLE seat_logs (
  id SERIAL PRIMARY KEY,
  seat_id INT REFERENCES seats(id),
  user_id INT REFERENCES users(id),
  check_in TIMESTAMP NOT NULL,
  check_out TIMESTAMP,
  pass_type VARCHAR(20),
  created_at TIMESTAMP DEFAULT NOW()
);
```

### QR Codes

```sql
CREATE TABLE qr_codes (
  id SERIAL PRIMARY KEY,
  code VARCHAR(255) UNIQUE NOT NULL,
  user_id INT REFERENCES users(id),
  seat_id INT REFERENCES seats(id),
  created_at TIMESTAMP DEFAULT NOW(),
  expires_at TIMESTAMP,
  used BOOLEAN DEFAULT false,
  used_at TIMESTAMP
);
```

### Door Logs

```sql
CREATE TABLE door_logs (
  id SERIAL PRIMARY KEY,
  room_id INT REFERENCES rooms(id),
  event VARCHAR(20) NOT NULL, -- 'open', 'close'
  user_id INT REFERENCES users(id),
  timestamp TIMESTAMP DEFAULT NOW()
);
```

### Board Notify

```sql
CREATE TABLE board_notify (
  id SERIAL PRIMARY KEY,
  room_id INT REFERENCES rooms(id),
  title VARCHAR(200),
  content TEXT,
  author INT REFERENCES admins(id),
  created_at TIMESTAMP DEFAULT NOW()
);
```

### Board Inquiry

```sql
CREATE TABLE board_inquiry (
  id SERIAL PRIMARY KEY,
  user_id INT REFERENCES users(id),
  content TEXT,
  status VARCHAR(20) DEFAULT 'pending',
  reply TEXT,
  reply_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW()
);
```

## Tech Stack

```
Backend:
- FastAPI (Python) or Express (Node.js)
- SQLAlchemy or Prisma (ORM)
- JWT (PyJWT or jsonwebtoken)
- mqtt.js or paho-mqtt

MQTT Broker:
- Mosquitto
- Config: allow_anonymous false, password_file

Database:
- PostgreSQL (recommended) or SQLite

Dependencies:
- QR generation: qrcode library
- Email sending: SMTP (nodemailer or smtplib)

Deploy:
- systemd service: backend.service
- Mosquitto systemd service
```

## Implementation Priority

```
1. [Urgent] DB schema, MQTT broker setup, auth/login, room/seats endpoints
2. [High] QR generation + verify, seat logs, door logs, admin auth
3. [Medium] User management, blacklist, kiosk/door register
4. [Low] Board endpoints, email sending, password reset
```

## Notes

- QR 서명: HMAC-SHA256 (backend secret key) — 위조 방지
- MQTT broker는 인증 필요 — username/password 설정
- SQLite는 Raspberry Pi에서 lightweight — PostgreSQL은 확장성 위해
- firmware와 통신: MQTT + REST (auth/verify만 REST)