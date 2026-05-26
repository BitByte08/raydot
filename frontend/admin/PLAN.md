# Admin Web — PLAN

관리자용 웹 페이지. `frontend/admin` 디렉터리. Vue 3 SPA, Raspberry Pi 4에서 Nginx로 서빙.

## Platform

- **Framework**: Vue 3 + Vite SPA
- **Access**: 학교 내부 네트워크 (VPN or campus WiFi)
- **Auth**: 관리자(교직원) 전용 — 학교 이메일 + 비밀번호
- **Backend**: `backend/` 서비스와 통신 (REST API + MQTT WebSocket)

## Feature Breakdown

### 1. Auth (관리자 인증)

#### 1.1 sign-up — High
관리자 회원가입

```
플로우:
1. 고유 식별코드 입력 (학교에서 발급)
2. 학교 이메일 입력 → 이메일 인증
3. 비밀번호 설정 → 계정 생성

UI:
- 식별코드 input
- 이메일: @school.edu 도메인만 허용
- 인증: "이메일로 인증 링크 발송"

API:
POST /api/admin/sign-up { code, email, password }
POST /api/admin/verify-email { token }
```

#### 1.2 login — Urgent
관리자 로그인

```
UI:
- 이메일 + 비밀번호 input
- "로그인" 버튼

API:
POST /api/admin/login { email, password }
  Response: { token, admin: { id, name, role } }
```

### 2. User (사용자 관리)

#### 2.1 create — High
학생 정보 생성

```
UI:
- 이메일, 학번, 이름 input
- "생성" 버튼

API:
POST /api/admin/user/create { email, student_id, name, pin? }
```

#### 2.2 list — Medium
전체 사용자 목록 (학년별 필터링)

```
UI:
- 테이블: 학번 | 이름 | 이메일 | 블랙리스트 | 이용권
- 학년 필터 dropdown

API:
GET /api/admin/users?grade={grade}
```

#### 2.3 log — High
특정 사용자 이용 기록

```
UI:
- 사용자 선택 → 기록 리스트
- 날짜 | 입실 | 퇴실 | 좌석 | QR 발급 여부

API:
GET /api/admin/user/{student_id}/logs
```

#### 2.4 blacklist — Medium
블랙리스트 등록/해제

```
UI:
- 기간 select: 1주 / 1개월 / 영구
- 사유 textarea
- 등록/해제 버튼

API:
POST /api/admin/user/{student_id}/blacklist { duration, reason }
DELETE /api/admin/user/{student_id}/blacklist
```

### 3. Room (정독실 관리)

#### 3.1 kiosk/register — Urgent
키오스크 연결

```
UI:
- 정독실 코드 input + "연결" 버튼
- 연결 상태 표시

API:
POST /api/admin/room/{room_code}/kiosk/register
MQTT Subscribe: kiosk/{room_code}/status
```

#### 3.2 kiosk/status — Urgent
키오스크 네트워크 상태

```
UI:
- 상태 카드: 녹색(연결) / 빨강(끊김)
- 마지막 ping 시간
```

#### 3.3 desk/create — Medium
좌석 배치 생성

```
UI:
- Grid editor: drag & drop 좌석 배치
- 슬롯 추가/삭제
- 슬롯 설정: 번호, 사용 불가능 toggle

API:
POST /api/admin/room/create { code, name, seats[] }
PUT /api/admin/room/{room_code}/seats
```

#### 3.4 desk/list — Urgent
전체 좌석 목록 (정독실별 필터)

#### 3.5 desk/state — Urgent
특정 좌석 상태 + 관리자 "사용 불가능" toggle

```
API:
GET /api/admin/room/{room_code}/seat/{seat_id}
PUT /api/admin/room/{room_code}/seat/{seat_id}/disable
```

#### 3.6 desk/log — High
좌석별 이용 기록

#### 3.7 door/register — Medium
출입문-정독실 연결

```
API:
POST /api/admin/room/{room_code}/door/register { door_id }
```

#### 3.8 door/state — High
실시간 출입문 상태 (MQTT Subscribe)

```
UI:
- 상태 카드: 연결 + 열림/닫힘
- 마지막 개폐 시간
```

#### 3.9 door/log — High
출입문 개폐 기록

```
API:
GET /api/admin/room/{room_code}/door/logs
```

### 4. QR

#### 4.1 — Medium
전체 QR 상태 조회 (사용됨/미사용 필터)

```
API:
GET /api/admin/qr?status={used|unused}
```

### 5. Board

#### 5.1 notify — Low
공지사항 등록/수정/삭제 (마크다운 지원, 최대 개수 제한)

#### 5.2 inquiry — Low
사용자 문의사항 — 답변 작성 (글자 수 제한), 답변 없이 삭제 가능

## Dashboard

```
메인 화면:
- 정독실 상태 카드: 키오스크 + 출입문 연결 상태
- 사용자 수: 전체 + 블랙리스트
- 좌석 현황 grid (실시간 MQTT)
- QR 사용률: 당일 발급/사용 수

Navigation: Dashboard | User | Room | QR | Board
```

## Implementation Priority

```
1. [Urgent] auth/login, kiosk/register, kiosk/status, desk/list, desk/state
2. [High] sign-up, user/create, user/log, door/state, door/log, desk/log
3. [Medium] user/list, blacklist, desk/create, door/register
4. [Low] QR, board/notify, board/inquiry
```

## Notes

- 와이어프레임 MCP 제공 예정 — UI 디자인은 그 후 진행
- kiosk와 admin은 같은 frontend 레포에 있지만 빌드/배포 분리
- admin은 Nginx reverse proxy → HTTPS 적용