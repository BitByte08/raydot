# EMLock 제어 구현

## 요구사항

- GPIO Relay 제어 기반 EMLock 열림/닫힘 제어

## 하드웨어

### 전자석 도어락 (EMLock)

| 타입 | 전압 | 전류 | 특징 |
|------|------|------|------|
| Fail-Safe | 12V DC | 0.5A | 전원 끊기면 열림 |
| Fail-Secure | 12V DC | 0.5A | 전원 끊기면 잠김 |

**권장: Fail-Safe** (비상시 자동 해제)

### 릴레이 모듈

| 핀 | 용도 | ESP32 핀 |
|---|------|----------|
| VCC | 전원 | 5V |
| GND | 그라운드 | GND |
| IN | 제어 신호 | GPIO 32 |

```cpp
#define EMLOCK_PIN 32
#define EMLOCK_ACTIVE_LOW true  // 릴레이 모듈에 따라 다름
```

### 회로도

```
ESP32                    Relay Module              EMLock
  │                          │                       │
  ├── GPIO 32 ───────────────┤ IN                    │
  │                          │                       │
  ├── 5V ───────────────────┤ VCC                   │
  │                          │                    ├──┤
  ├── GND ──────────────────┤ GND                 │  │
  │                          │    COM ─────────────┤  │ 12V
  │                          │    NO  ─────────────┤  │
  │                          │                       │
                                                        GND (12V)
```

## EMLockManager 클래스

```cpp
#pragma once
#include <Arduino.h>

enum class LockState {
    LOCKED,    // 잠김 (닫힘)
    UNLOCKED   // 열림
};

class EMLockManager {
public:
    void begin();
    void open(unsigned long duration = 5000);  // 기본 5초
    void close();
    void update();  // 타이머 체크용, loop에서 호출
    
    LockState getState();
    bool isOpen();
    
    // 콜백
    void setOnOpenCallback(void (*callback)());
    void setOnCloseCallback(void (*callback)());
    
private:
    int pin;
    bool activeLow;
    LockState state;
    unsigned long openTime;
    unsigned long openDuration;
    bool timerActive;
    
    void (*onOpenCallback)() = nullptr;
    void (*onCloseCallback)() = nullptr;
    
    void setLock(bool locked);
};

extern EMLockManager emlockManager;
```

## 구현

```cpp
#include "EMLockManager.h"

#define EMLOCK_PIN 32
#define EMLOCK_ACTIVE_LOW true

EMLockManager emlockManager;

void EMLockManager::begin() {
    pin = EMLOCK_PIN;
    activeLow = EMLOCK_ACTIVE_LOW;
    
    pinMode(pin, OUTPUT);
    setLock(true);  // 초기 상태: 잠금
    
    state = LockState::LOCKED;
    timerActive = false;
}

void EMLockManager::open(unsigned long duration) {
    setLock(false);  // 열림
    state = LockState::UNLOCKED;
    openTime = millis();
    openDuration = duration;
    timerActive = true;
    
    if (onOpenCallback) {
        onOpenCallback();
    }
    
    Serial.printf("EMLock opened for %lu ms\n", duration);
}

void EMLockManager::close() {
    setLock(true);  // 잠금
    state = LockState::LOCKED;
    timerActive = false;
    
    if (onCloseCallback) {
        onCloseCallback();
    }
    
    Serial.println("EMLock closed");
}

void EMLockManager::update() {
    if (timerActive && state == LockState::UNLOCKED) {
        if (millis() - openTime >= openDuration) {
            close();
        }
    }
}

LockState EMLockManager::getState() {
    return state;
}

bool EMLockManager::isOpen() {
    return state == LockState::UNLOCKED;
}

void EMLockManager::setLock(bool locked) {
    if (activeLow) {
        digitalWrite(pin, locked ? HIGH : LOW);  // Active Low: HIGH = 잠금
    } else {
        digitalWrite(pin, locked ? LOW : HIGH);   // Active High: LOW = 잠금
    }
}

void EMLockManager::setOnOpenCallback(void (*callback)()) {
    onOpenCallback = callback;
}

void EMLockManager::setOnCloseCallback(void (*callback)()) {
    onCloseCallback = callback;
}
```

## 안전 기능

### 1. 와치독 타이머

```cpp
#include <esp_task_wdt.h>

void EMLockManager::begin() {
    // 30초 와치독
    esp_task_wdt_init(30, true);
    esp_task_wdt_add(NULL);
    
    // 기존 초기화...
}

void EMLockManager::update() {
    esp_task_wdt_reset();  // 와치독 리셋
    
    // 기존 타이머 체크...
}
```

### 2. 비상 해제 (Fail-Safe)

```cpp
void EMLockManager::emergencyRelease() {
    // 모든 타이머 무시하고 즉시 해제
    setLock(false);
    state = LockState::UNLOCKED;
    timerActive = false;
    Serial.println("EMERGENCY: EMLock released!");
}
```

### 3. 수동 제어 버튼 (선택적)

```cpp
#define MANUAL_BUTTON_PIN 34

void setup() {
    emlockManager.begin();
    pinMode(MANUAL_BUTTON_PIN, INPUT_PULLUP);
}

void loop() {
    emlockManager.update();
    
    // 수동 버튼 체크
    if (digitalRead(MANUAL_BUTTON_PIN) == LOW) {
        emlockManager.open(5000);
    }
}
```

## main.cpp 통합

```cpp
#include "EMLockManager.h"
#include "MQTTManager.h"
#include "UIManager.h"

void onDoorOpen() {
    uiManager.showScreen(Screen::OPENED);
    mqttManager.publishLockState(LockState::UNLOCKED);
    mqttManager.publishEvent("door_open", "manual");
}

void onDoorClose() {
    uiManager.showScreen(Screen::CLOSED);
    mqttManager.publishLockState(LockState::LOCKED);
    mqttManager.publishEvent("door_close", "timer");
}

void setup() {
    emlockManager.begin();
    emlockManager.setOnOpenCallback(onDoorOpen);
    emlockManager.setOnCloseCallback(onDoorClose);
}

void loop() {
    emlockManager.update();
}

// QR 인증 성공 시
void onAuthSuccess(AuthResult result) {
    uiManager.setUserName(result.userName);
    emlockManager.open(result.openDuration * 1000);
}
```

## 타이머 UI 연동

```cpp
void loop() {
    emlockManager.update();
    
    // UI 타이머 업데이트
    if (emlockManager.isOpen()) {
        unsigned long remaining = emlockManager.getRemainingTime();
        uiManager.setOpenTimer(remaining / 1000, emlockManager.getDuration() / 1000);
    }
}
```

## 추가 메서드

```cpp
// EMLockManager.h에 추가
unsigned long getRemainingTime();
unsigned long getDuration();

// EMLockManager.cpp에 추가
unsigned long EMLockManager::getRemainingTime() {
    if (!timerActive || state == LockState::LOCKED) {
        return 0;
    }
    
    unsigned long elapsed = millis() - openTime;
    if (elapsed >= openDuration) {
        return 0;
    }
    
    return openDuration - elapsed;
}

unsigned long EMLockManager::getDuration() {
    return openDuration;
}
```

## 파일 구조

```
src/
├── lock/
│   ├── EMLockManager.h
│   └── EMLockManager.cpp
└── main.cpp
```

## 하드웨어 연결 상세

### 릴레이 모듈 종류

| 타입 | Active | 설명 |
|------|--------|------|
| Active Low | LOW = ON | 대부분의 릴레이 모듈 |
| Active High | HIGH = ON | 일부 모델 |

### 권장 릴레이 모듈

- 5V Relay Module (1채널)
- Opto-isolated Relay (노이즈 보호)
- SSR (Solid State Relay) - 무접점, 수명 김

### 주의사항

1. **역기전력 보호**: 릴레이 코일에 다이오드 병렬 연결 (내장된 경우 많음)
2. **전원 분리**: ESP32와 EMLock 전원 분리 권장
3. **GND 공통**: ESP32와 EMLock GND는 공통 필요
4. **전류 용량**: EMLock 전류에 맞는 릴레이 선택 (최소 1A 권장)