# LCD Interface 구현

## 요구사항

- 정독실 등록 대기/완료 화면
- 닫힘 화면 (QR 대기)
- 열림 화면

## 화면 정의

### 1. 등록 대기 화면 (registration)
- 시스템 미등록 시 표시
- QR 스캔 안내

### 2. 등록 완료 화면 (registered)
- 등록 성공 시 표시
- 재부팅 안내

### 3. 닫힘 화면 (closed)
- 문 닫힘 상태
- QR 스캔 대기
- MQTT 연결 상태 표시

### 4. 열림 화면 (opened)
- 문 열림 상태
- 남은 시간 표시
- 타이머 진행바

### 5. 에러 화면 (error)
- 네트워크 연결 실패
- MQTT 연결 실패
- 기타 에러

## UI JSON 정의

```cpp
const char UI_JSON[] PROGMEM = R"({
  "version": "1.0",
  "display": { "width": 320, "height": 240, "rotation": 1 },
  "screens": [
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
          "x": 160, "y": 200,
          "text": "Reset 스위치: 설정 초기화",
          "style": { "color": "#666666", "fontSize": 1, "align": "center" }
        }
      ]
    },
    {
      "id": "registered",
      "background": "#1A1A2E",
      "components": [
        {
          "type": "label",
          "id": "lbl_title",
          "x": 160, "y": 60,
          "text": "등록 완료",
          "style": { "color": "#00FF00", "fontSize": 3, "align": "center" }
        },
        {
          "type": "label",
          "id": "lbl_room",
          "x": 160, "y": 120,
          "text": "정독실: ---",
          "style": { "color": "#FFFFFF", "fontSize": 2, "align": "center" }
        },
        {
          "type": "label",
          "id": "lbl_reboot",
          "x": 160, "y": 180,
          "text": "시스템 재시작 중...",
          "style": { "color": "#00B4D8", "fontSize": 2, "align": "center" }
        }
      ]
    },
    {
      "id": "closed",
      "background": "#1A1A2E",
      "components": [
        {
          "type": "label",
          "id": "lbl_room",
          "x": 160, "y": 20,
          "text": "정독실: ---",
          "style": { "color": "#FFFFFF", "fontSize": 2, "align": "center" }
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
          "id": "lbl_mqtt",
          "x": 10, "y": 220,
          "text": "MQTT: ---",
          "style": { "color": "#666666", "fontSize": 1 }
        },
        {
          "type": "label",
          "id": "lbl_wifi",
          "x": 200, "y": 220,
          "text": "WiFi: ---",
          "style": { "color": "#666666", "fontSize": 1 }
        }
      ]
    },
    {
      "id": "opened",
      "background": "#0D3B66",
      "components": [
        {
          "type": "label",
          "id": "lbl_title",
          "x": 160, "y": 20,
          "text": "문 열림",
          "style": { "color": "#00FF00", "fontSize": 3, "align": "center" }
        },
        {
          "type": "label",
          "id": "lbl_timer",
          "x": 160, "y": 80,
          "text": "5초",
          "style": { "color": "#FFFFFF", "fontSize": 4, "align": "center" }
        },
        {
          "type": "slider",
          "id": "sld_progress",
          "x": 40, "y": 140,
          "min": 0, "max": 100, "value": 100
        },
        {
          "type": "label",
          "id": "lbl_user",
          "x": 160, "y": 200,
          "text": "사용자: ---",
          "style": { "color": "#CCCCCC", "fontSize": 1, "align": "center" }
        }
      ]
    },
    {
      "id": "error",
      "background": "#2D1B1B",
      "components": [
        {
          "type": "label",
          "id": "lbl_title",
          "x": 160, "y": 40,
          "text": "에러",
          "style": { "color": "#FF4444", "fontSize": 3, "align": "center" }
        },
        {
          "type": "label",
          "id": "lbl_error",
          "x": 160, "y": 100,
          "text": "에러 메시지",
          "style": { "color": "#FFFFFF", "fontSize": 2, "align": "center" }
        },
        {
          "type": "button",
          "id": "btn_retry",
          "x": 90, "y": 160, "width": 140, "height": 50,
          "label": "재시도",
          "style": { "bg": "#00B4D8", "text": "#FFFFFF", "radius": 8 },
          "onPress": "retry"
        }
      ]
    }
  ]
})";
```

## UIManager 클래스

```cpp
#pragma once
#include <NanoUI.h>
#include "ConfigManager.h"

enum class Screen {
    REGISTRATION,
    REGISTERED,
    CLOSED,
    OPENED,
    ERROR
};

class UIManager {
public:
    void begin();
    void update();
    void showScreen(Screen screen);
    void setRoomCode(const String& code);
    void setMQTTStatus(bool connected);
    void setWiFiStatus(bool connected);
    void setOpenTimer(int seconds, int total);
    void setUserName(const String& name);
    void showError(const String& message);
    
private:
    NanoUI::NanoUI ui;
    Screen currentScreen;
    String roomCode;
    
    void updateStatusLabel(const char* id, const char* text, const char* color);
};

extern UIManager uiManager;
```

## 핀 설정

SPI 모드 사용 (기본 핀):

| 핀 | 용도 | 기본값 |
|---|------|--------|
| TFT_CS | LCD 칩 선택 | 10 |
| TFT_DC | 데이터/명령 | 9 |
| TFT_RST | 리셋 | 8 |
| TOUCH_CS | 터치 칩 선택 | 7 |

```cpp
void UIManager::begin() {
    ui.begin();  // 기본 핀 사용
    ui.loadFromFlash(UI_JSON);
    showScreen(Screen::REGISTRATION);
}
```

## 화면 전환 로직

```cpp
void UIManager::showScreen(Screen screen) {
    currentScreen = screen;
    
    switch (screen) {
        case Screen::REGISTRATION:
            ui.show("registration");
            break;
        case Screen::REGISTERED:
            ui.show("registered");
            ui.setText("lbl_room", ("정독실: " + roomCode).c_str());
            break;
        case Screen::CLOSED:
            ui.show("closed");
            ui.setText("lbl_room", ("정독실: " + roomCode).c_str());
            break;
        case Screen::OPENED:
            ui.show("opened");
            break;
        case Screen::ERROR:
            ui.show("error");
            break;
    }
}
```

## 타이머 표시

```cpp
void UIManager::setOpenTimer(int seconds, int total) {
    String timerText = String(seconds) + "초";
    ui.setText("lbl_timer", timerText.c_str());
    
    int progress = (seconds * 100) / total;
    ui.setValue("sld_progress", progress);
}
```

## 상태 표시

```cpp
void UIManager::setMQTTStatus(bool connected) {
    updateStatusLabel("lbl_mqtt", 
        connected ? "MQTT: 연결됨" : "MQTT: 연결 끊김",
        connected ? "#00FF00" : "#FF4444");
}

void UIManager::setWiFiStatus(bool connected) {
    updateStatusLabel("lbl_wifi",
        connected ? "WiFi: 연결됨" : "WiFi: 연결 끊김",
        connected ? "#00FF00" : "#FF4444");
}
```

## 파일 구조

```
src/
├── ui/
│   ├── UIManager.h
│   ├── UIManager.cpp
│   └── screens.h      // UI_JSON 정의
└── main.cpp
```