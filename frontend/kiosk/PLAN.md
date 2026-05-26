# Frontend (Kiosk UI) — PLAN

학생용 키오스크 앱. Raspberry Pi 4에서 Electron + Vue/React로 실행.

## Platform

- **Runtime**: Raspberry Pi 4, kiosk mode (fullscreen, no cursor)
- **Framework**: Electron + Vue 3 or React
- **Display**: 7-10 inch touchscreen LCD
- **Input**: RFID/Barcode scanner (USB or UART), touchscreen

## Feature Breakdown

### 1. Auth (로그인)

#### 1.1 login — Urgent
학생증 정보 기반 로그인

```
플로우:
1. RFID/바코드 스캔 → 학생 ID 식별
2. 비밀번호 입력 dialog (4자리 PIN)
3. Backend auth API 호출 → JWT token 발급
4. 블랙리스트 확인 → 제한 안내 alert (if blacklisted)
5. 성공 → 사용자 정보 저장 → seat/state 화면으로 전환

UI:
- 학생증 스캔 안내 화면 (RFID/바코드 아이콘)
- PIN 입력: 4-digit keypad overlay
- 블랙리스트 alert: "정독실 이용이 제한되었습니다. 관리자에게 문의하세요."

API:
POST /api/auth/login
  Body: { student_id: string, pin: string }
  Response: { success: bool, user: User, blacklist: bool, token: string }
```

#### 1.2 password/initial — High
최초 비밀번호 설정

```
플로우:
1. 학생증 스캔 → 학생 ID 식별
2. Backend 확인 → password_set == false
3. PIN 설정 dialog (4-digit)
4. 저장 → password_set = true

UI:
- PIN 설정: "최초 비밀번호 설정" title
- 4-digit keypad + 확인/취소 버튼

API:
POST /api/auth/password/initial
  Body: { student_id: string, pin: string }
```

#### 1.3 password/find — Low
비밀번호 찾기

```
플로우:
1. 학생증 스캔 → 학생 ID 식별
2. Backend 호출 → 등록된 email로 재설정 URL 발송
3. 안내 화면: "이메일로 재설정 링크가 발송되었습니다."

API:
POST /api/auth/password/find
  Body: { student_id: string }
```

### 6. User (사용자 정보)

#### 6.1 info — Low
사용자 정보 확인

```
UI:
- 학번, 이름 (필수)
- 이메일, 기타 정보 (optional)
- 하단: "이용 기록" 버튼

API:
GET /api/user/{student_id}
```

#### 6.2 log — High
사용자 이용 기록 (지난 1달)

```
UI:
- 리스트: 날짜 | 입실 시간 | 퇴실 시간 | 좌석 번호
- 필터: 최근 7일 / 14일 / 30일

API:
GET /api/user/{student_id}/logs?range=30d
```

#### 6.3 password/reset — Low
비밀번호 재설정

```
UI:
- 현재 PIN 입력
- 새 PIN 입력 (4-digit)
- 새 PIN 확인
- 저장 버튼

API:
POST /api/user/{student_id}/password/reset
  Body: { current_pin: string, new_pin: string }
```

### 8. Desk (좌석 현황)

#### 8.1 state — Urgent
전체 좌석 현황

```
UI:
- Grid layout: 좌석 슬롯 시각화
- 슬롯 상태:
  - empty (회색): 사용 가능
  - occupied (파랑): 입실 중
  - disabled (빨강): 관리자 지정 사용 불가
- 각 슬롯: 번호 표시

API:
GET /api/room/{room_code}/seats
  Response: { seats: [{ id, number, status, user_id?, user_name? }] }
```

#### 8.2 move — Medium
타 좌석 이동

```
플로우:
1. 현재 좌석 선택 → "이동" 버튼 활성화 (입실 중일 때만)
2. 이동할 좌석 선택 → 확인 dialog
3. Backend 호출 → 좌석 이동 처리

UI:
- 이동 버튼: 로그인 상태 + 입실 중 → 활성화
- 이동 dialog: "A03 → B05로 이동하시겠습니까?"

API:
POST /api/room/{room_code}/seat/move
  Body: { from_seat_id, to_seat_id, user_id }
```

### 10. Check-in (입실)

#### 10.1 select — Urgent
입실 좌석 선택

```
플로우:
1. 빈 좌석 선택 → 입실 dialog
2. 이용권 선택: 당일권 / 정기권(주간, 월간)
3. Backend 호출 → 입실 등록
4. QR 발급 → 화면 표시 + 이메일 발송

UI:
- 좌석 선택 → "입실" 버튼 (empty 상태에서만)
- 이용권 선택: radio buttons
- QR 표시: QR 코드 이미지 + "이메일로 발송됨" 안내

API:
POST /api/room/{room_code}/check-in
  Body: { seat_id, user_id, pass_type: "daily"|"weekly"|"monthly" }
  Response: { success, qr_code, expires_at }
```

#### 10.2 qr — Urgent
입장 QR 발급

```
QR Format:
USER:{user_id}:{seat_id}:{timestamp}:{signature}

UI:
- QR 이미지 (화면 중앙)
- "정독실 입장 시 QR을 스캔하세요" 안내
- 이메일 발송 확인

API:
GET /api/qr/{qr_id}
  Response: { qr_image_url, valid_until }
```

### 12. Check-out (퇴실)

#### 12.1 — Urgent
퇴실 처리

```
플로우:
1. 입실 중 좌석 선택 → "퇴실" 버튼
2. 확인 dialog → Backend 호출
3. QR 입장 불가능 처리

UI:
- 퇴실 버튼: occupied 상태에서만
- 퇴실 dialog: "A03 좌석에서 퇴실하시겠습니까?"

API:
POST /api/room/{room_code}/check-out
  Body: { seat_id, user_id }
```

### 13. Board (게시판)

#### 13.1 notify — Low
공지사항

```
UI:
- 리스트: 제목 | 날짜 | 관리자명
- 상세: 마크다운 렌더링

API:
GET /api/board/notify?room_code={room_code}
```

#### 13.2 inquiry — Low
문의사항

```
UI:
- 문의 등록: textarea + 제출 버튼
- 내 문의 리스트: 문제 | 답변 상태 | 답변 내용

API:
POST /api/board/inquiry
  Body: { user_id, content }
GET /api/board/inquiry/{user_id}
```

## State Management

```
전역 상태 (Vuex/Pinia):
- user: { id, name, student_id, email, blacklist }
- room: { code, name, seats[] }
- current_seat: { id, number, status }
- auth: { token, logged_in }

로컬 상태:
- screen: 현재 화면 (login | desk | check-in | check-out | board)
- pass_type: 당일권/정기권 선택
```

## Screen Flow

```
Boot → Splash → Login
         │
         ├─ Blacklist? → Alert → Login
         │
         └─ Success → Desk (state)
                        │
                        ├─ Select empty seat → Check-in → QR display → Desk
                        ├─ Select occupied seat (mine) → Check-out → Desk
                        ├─ Select occupied seat (mine) → Move → Desk
                        ├─ Menu → User Info
                        ├─ Menu → User Log
                        ├─ Menu → Board (notify/inquiry)
```

## Tech Stack

```
Frontend:
- Vue 3 + Vite or React + Next.js
- Electron (kiosk mode)
- Pinia or Redux (state)
- Axios (HTTP)
- mqtt.js (MQTT client)

Dependencies:
- QR code generator: qrcode library
- RFID/Barcode scanner: serialport or USB HID

Build:
- npm run build → dist/
- electron-builder → kiosk.app
```

## Implementation Priority

```
1. [Urgent] auth/login, desk/state, check-in/select, check-out
2. [High] password/initial, user/log
3. [Medium] desk/move
4. [Low] password/find, user/info, password/reset, board/*
```

## Notes

- 와이어프레임 MCP 제공 예정 — UI 디자인은 그 후 진행
- RFID scanner는 USB HID로 인식 → keyboard event로 입력됨
- MQTT로 실시간 좌석 상태 업데이트 필요 (kiosk/{roomCode}/seat/state subscribe)