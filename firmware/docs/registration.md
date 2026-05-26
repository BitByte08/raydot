# 정독실 등록 (Registration)

## 요구사항

- 시스템 최초 실행 시 진행
- 등록된 정보 없을 시 타 기능 미실행
- 정독실 식별코드 입력 시, 해당 정독실로 시스템 정보 종속
- 정보 전송 방식 고안 필요
- **Reset Switch 배치 필요**

## 구현 방안

### 1. 등록 정보 저장

ESP32 `Preferences` 라이브러리 사용하여 NVS(Non-Volatile Storage)에 저장.

```cpp
#include <Preferences.h>
Preferences prefs;

// 저장
prefs.begin("door", false);
prefs.putString("room_code", roomCode);
prefs.end();

// 불러오기
prefs.begin("door", true);
String roomCode = prefs.getString("room_code", "");
prefs.end();
```

### 2. 등록 프로세스

```
시작
  │
  ▼
[Preferences에서 room_code 조회]
  │
  ├── 존재 → 등록 완료 상태 → 메인 루프 진입
  │
  └── 없음 → 등록 대기 화면 표시
                │
                ▼
          [QR 스캔 대기]
                │
                ├── QR 스캔 (식별코드 형식)
                │     │
                │     ▼
                │   [서버에 등록 요청 (MQTT)]
                │     │
                │     ├── 성공 → Preferences 저장 → 재부팅
                │     └── 실패 → 에러 메시지 표시
                │
                └── Reset Switch 누름 → BLE/WiFi 설정 모드 진입
```

### 3. Reset Switch

| 목적 | 동작 |
|------|------|
| **초기화** | 5초 이상 길게 누름 → 모든 설정 초기화 |
| **설정 모드** | 짧게 누름 → BLE/WiFi 설정 모드 진입 |

```cpp
#define RESET_PIN 33

void setup() {
    pinMode(RESET_PIN, INPUT_PULLUP);
    
    // 길게 누름 감지 (5초)
    if (digitalRead(RESET_PIN) == LOW) {
        delay(5000);
        if (digitalRead(RESET_PIN) == LOW) {
            // 설정 초기화
            Preferences prefs;
            prefs.begin("door", false);
            prefs.clear();
            prefs.end();
        }
    }
}
```

### 4. 정보 전송 방식

#### 제안 1: BLE → WiFi 정보 전송
- 스마트폰 앱에서 BLE로 연결
- WiFi credentials 전송
- Reset Switch로 BLE 모드 진입

#### 제안 2: ETH (LAN선) - 채택
- 유선 연결로 더 안정적
- 별도 설정 없이 연결
- DHCP 자동 IP 할당

```cpp
// ETH 초기화 (W5500)
#include <Ethernet.h>
byte mac[] = { 0xDE, 0xAD, 0xBE, 0xEF, 0xFE, 0xED };

void initEthernet() {
    Ethernet.init(5);  // CS 핀
    Ethernet.begin(mac);
    
    if (Ethernet.linkStatus() == LinkON) {
        Serial.println("Ethernet connected");
    }
}
```

### 5. QR 코드 형식

정독실 식별코드 QR 형식:

```
ROOM:정독실코드
예: ROOM:BSSM-A101
```

```cpp
bool parseRoomCode(const String& qrData, String& roomCode) {
    if (qrData.startsWith("ROOM:")) {
        roomCode = qrData.substring(5);
        return true;
    }
    return false;
}
```

## 상태 관리

```cpp
enum class RegistrationState {
    UNREGISTERED,    // 미등록
    WAITING_CODE,    // 코드 입력 대기
    REGISTERING,     // 등록 진행 중
    REGISTERED,      // 등록 완료
    ERROR            // 에러
};

RegistrationState regState = RegistrationState::UNREGISTERED;
```

## UI 화면

### 등록 대기 화면

```json
{
  "id": "registration",
  "background": "#1A1A2E",
  "components": [
    {
      "type": "label",
      "id": "lbl_title",
      "x": 160, "y": 40,
      "text": "정독실 등록",
      "style": { "color": "#FFFFFF", "fontSize": 3, "align": "center" }
    },
    {
      "type": "label",
      "id": "lbl_status",
      "x": 160, "y": 100,
      "text": "QR 코드를 스캔하세요",
      "style": { "color": "#00B4D8", "fontSize": 2, "align": "center" }
    },
    {
      "type": "label",
      "id": "lbl_hint",
      "x": 160, "y": 180,
      "text": "Reset 스위치: 설정 초기화",
      "style": { "color": "#666666", "fontSize": 1, "align": "center" }
    }
  ]
}
```

### 등록 완료 화면

```json
{
  "id": "registered",
  "background": "#1A1A2E",
  "components": [
    {
      "type": "label",
      "id": "lbl_title",
      "x": 160, "y": 40,
      "text": "등록 완료",
      "style": { "color": "#00FF00", "fontSize": 3, "align": "center" }
    },
    {
      "type": "label",
      "id": "lbl_room",
      "x": 160, "y": 100,
      "text": "정독실: 코드",
      "style": { "color": "#FFFFFF", "fontSize": 2, "align": "center" }
    },
    {
      "type": "label",
      "id": "lbl_reboot",
      "x": 160, "y": 160,
      "text": "시스템 재시작 중...",
      "style": { "color": "#00B4D8", "fontSize": 2, "align": "center" }
    }
  ]
}
```

## 코드 구조

```
src/
├── config/
│   ├── ConfigManager.h
│   └── ConfigManager.cpp
└── main.cpp
```

### ConfigManager.h

```cpp
#pragma once
#include <Arduino.h>
#include <Preferences.h>

struct DoorConfig {
    String roomCode;
    String wifiSSID;
    String wifiPass;
    String mqttServer;
    int mqttPort;
    bool isRegistered;
};

class ConfigManager {
public:
    void begin();
    bool load();
    bool save(const DoorConfig& config);
    void clear();
    DoorConfig getConfig();
    bool isRegistered();
    
private:
    Preferences prefs;
    DoorConfig config;
};

extern ConfigManager configManager;
```