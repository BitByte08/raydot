# QR Scanner 입력 구현

## 요구사항

- 읽기 속도 제한 필요 (너무 빠른/많은 읽기 제한)

## 하드웨어

### QR 스캐너 모듈

대부분의 QR 스캐너는 USB HID 또는 UART 시리얼로 데이터를 전송합니다.

ESP32에서는 UART(Serial) 방식 사용:

| 핀 | 용도 | ESP32 핀 |
|---|------|----------|
| VCC | 전원 | 5V |
| GND | 그라운드 | GND |
| TX | 데이터 송신 | GPIO 16 (RX2) |
| RX | 데이터 수신 | GPIO 17 (TX2) |

```cpp
#define QR_RX_PIN 16
#define QR_TX_PIN 17
```

## QRScanner 클래스

```cpp
#pragma once
#include <Arduino.h>

enum class QRType {
    ROOM_CODE,     // 정독실 코드 (ROOM:xxx)
    USER_CODE,     // 사용자 코드 (USER:xxx)
    UNKNOWN
};

struct QRData {
    QRType type;
    String code;
    String raw;
};

class QRScanner {
public:
    void begin();
    void update();
    bool hasNewCode();
    QRData getCode();
    void clearCode();
    
    // 속도 제한 설정
    void setMinInterval(unsigned long ms);
    
private:
    HardwareSerial* serial;
    String buffer;
    bool newCodeAvailable;
    unsigned long lastReadTime;
    unsigned long minInterval;  // 최소 읽기 간격 (ms)
    QRData lastCode;
    
    void processBuffer();
    QRType parseType(const String& data);
};

extern QRScanner qrScanner;
```

## 구현

```cpp
#include "QRScanner.h"

QRScanner qrScanner;

void QRScanner::begin() {
    serial = &Serial2;
    serial->begin(9600, SERIAL_8N1, QR_RX_PIN, QR_TX_PIN);
    
    buffer.reserve(256);
    newCodeAvailable = false;
    minInterval = 2000;  // 기본 2초 간격
    lastReadTime = 0;
}

void QRScanner::update() {
    while (serial->available()) {
        char c = serial->read();
        
        if (c == '\n' || c == '\r') {
            if (buffer.length() > 0) {
                processBuffer();
            }
        } else {
            buffer += c;
        }
    }
}

void QRScanner::processBuffer() {
    unsigned long now = millis();
    
    // 속도 제한: 마지막 읽기 후 minInterval이 지나지 않았으면 무시
    if (now - lastReadTime < minInterval) {
        buffer = "";
        return;
    }
    
    lastCode.raw = buffer;
    lastCode.type = parseType(buffer);
    
    // QR 타입에 따라 코드 추출
    switch (lastCode.type) {
        case QRType::ROOM_CODE:
            lastCode.code = buffer.substring(5);  // "ROOM:" 제거
            break;
        case QRType::USER_CODE:
            lastCode.code = buffer.substring(5);  // "USER:" 제거
            break;
        default:
            lastCode.code = buffer;
    }
    
    newCodeAvailable = true;
    lastReadTime = now;
    buffer = "";
}

QRType QRScanner::parseType(const String& data) {
    if (data.startsWith("ROOM:")) {
        return QRType::ROOM_CODE;
    } else if (data.startsWith("USER:")) {
        return QRType::USER_CODE;
    }
    return QRType::UNKNOWN;
}

bool QRScanner::hasNewCode() {
    return newCodeAvailable;
}

QRData QRScanner::getCode() {
    newCodeAvailable = false;
    return lastCode;
}

void QRScanner::clearCode() {
    newCodeAvailable = false;
    lastCode = QRData();
}

void QRScanner::setMinInterval(unsigned long ms) {
    minInterval = ms;
}
```

## 속도 제한 상세

### 문제 시나리오
1. 사용자가 같은 QR을 여러 번 찍음
2. QR 스캐너가 빠르게 연속 데이터 전송
3. 중복 인증 요청 발생

### 해결 방안

```cpp
// 1. 시간 기반 제한
void QRScanner::setMinInterval(unsigned long ms) {
    minInterval = ms;  // 기본 2000ms (2초)
}

// 2. 쿨다운 기간 중 무시
bool QRScanner::isInCooldown() {
    return (millis() - lastReadTime < minInterval);
}

// 3. 상태 머신과 연동
void onQRCodeReceived(QRData qr) {
    // 인증 진행 중이면 무시
    if (stateManager.getState() == State::AUTHENTICATING) {
        return;
    }
    
    // 정상 처리
    processQRCode(qr);
}
```

### 디바운싱 추가

```cpp
class QRScanner {
private:
    String lastCodeString;
    unsigned long lastCodeTime;
    const unsigned long debounceTime = 500;  // 500ms
    
    bool isDuplicate(const String& code) {
        if (code == lastCodeString && 
            millis() - lastCodeTime < debounceTime) {
            return true;
        }
        return false;
    }
};

void QRScanner::processBuffer() {
    // 디바운싱 체크
    if (isDuplicate(buffer)) {
        buffer = "";
        return;
    }
    
    // 속도 제한 체크
    if (millis() - lastReadTime < minInterval) {
        buffer = "";
        return;
    }
    
    // 정상 처리
    lastCodeString = buffer;
    lastCodeTime = millis();
    // ...
}
```

## QR 코드 형식

### 정독실 코드

```
ROOM:정독실식별코드
예: ROOM:BSSM-A101
예: ROOM:LIBRARY-203
```

### 사용자 코드

```
USER:사용자식별코드
예: USER:2024001
예: USER:MEMBER-12345
```

## main.cpp 통합

```cpp
#include "QRScanner.h"
#include "MQTTManager.h"
#include "UIManager.h"

void processQRCode(QRData qr) {
    switch (qr.type) {
        case QRType::ROOM_CODE:
            // 정독실 등록 처리
            if (configManager.isRegistered()) {
                uiManager.showError("이미 등록된 장치");
            } else {
                configManager.setRoomCode(qr.code);
                uiManager.showScreen(Screen::REGISTERED);
                delay(2000);
                ESP.restart();
            }
            break;
            
        case QRType::USER_CODE:
            // 사용자 인증 처리
            if (!configManager.isRegistered()) {
                uiManager.showError("먼저 정독실을 등록하세요");
                return;
            }
            if (!mqttManager.isConnected()) {
                uiManager.showError("네트워크 연결 없음");
                return;
            }
            // 인증 요청
            AuthResult result;
            mqttManager.requestAuth(qr.raw, result);
            break;
            
        default:
            uiManager.showError("알 수 없는 QR 코드");
    }
}

void setup() {
    qrScanner.begin();
    qrScanner.setMinInterval(2000);  // 2초 간격
}

void loop() {
    qrScanner.update();
    
    if (qrScanner.hasNewCode()) {
        QRData qr = qrScanner.getCode();
        processQRCode(qr);
    }
}
```

## 다양한 QR 스캐너 대응

### 일반적인 UART 설정

```cpp
// 대부분의 QR 스캐너
serial->begin(9600, SERIAL_8N1, QR_RX_PIN, QR_TX_PIN);

// 일부 모델 (예: ZEBRA)
serial->begin(115200, SERIAL_8N1, QR_RX_PIN, QR_TX_PIN);

// HID 모드 (USB) - USB Host Shield 필요
```

### 자동 감지

```cpp
void QRScanner::begin() {
    // 9600으로 시도
    Serial2.begin(9600, SERIAL_8N1, QR_RX_PIN, QR_TX_PIN);
    delay(100);
    
    // 데이터가 들어오면 성공
    // 실패 시 다른 보드레이트로 재시도 로직 추가 가능
}
```

## 파일 구조

```
src/
├── scanner/
│   ├── QRScanner.h
│   └── QRScanner.cpp
└── main.cpp
```

## 하드웨어 권장 모델

| 모델 | 인터페이스 | 특징 |
|------|-----------|------|
| ZKTeco ZK-800 | UART/USB | 저렴, 빠른 스캔 |
| Hikvision DS-6701 | UART/USB | 안정적 |
| Generic QR Module | UART | 아두이노 호환 |