# MQTT 연결 및 구독/발행

## 요구사항

- n초마다 연결 상태 발행 (kiosk 연결 상태와 동일)
- 현재 EMLock 열림/닫힘 상태 발행

## MQTT 구조

### 토픽 설계

```
door/{room_code}/status      → 장치 상태 발행 (연결, EMLock)
door/{room_code}/command     → 명령 수신 (잠금, 해제)
door/{room_code}/auth        → 인증 요청/응답
door/{room_code}/event       → 이벤트 (출입 기록)
```

### 상태 메시지 형식

```json
{
  "timestamp": 1234567890,
  "connected": true,
  "lock_state": "closed",
  "network": "ethernet",
  "ip": "192.168.1.100"
}
```

### 인증 요청 형식

```json
// 요청
{
  "action": "auth_request",
  "qr_code": "USER:123456",
  "timestamp": 1234567890
}

// 응답
{
  "action": "auth_response",
  "success": true,
  "user_name": "홍길동",
  "open_duration": 5,
  "timestamp": 1234567890
}
```

## MQTTManager 클래스

```cpp
#pragma once
#include <Arduino.h>
#include <PubSubClient.h>
#include "NetworkManager.h"
#include "ConfigManager.h"

enum class LockState {
    CLOSED,
    OPENED
};

struct AuthResult {
    bool success;
    String userName;
    int openDuration;
};

class MQTTManager {
public:
    void begin();
    void update();
    bool isConnected();
    
    // 상태 발행
    void publishStatus();
    void publishLockState(LockState state);
    void publishEvent(const String& eventType, const String& data);
    
    // 인증 요청
    bool requestAuth(const String& qrCode, AuthResult& result);
    
    // 상태 조회
    LockState getLockState();
    
    // 콜백
    void setOnAuthCallback(void (*callback)(AuthResult));
    void setOnCommandCallback(void (*callback)(const String& command));
    
private:
    PubSubClient mqttClient;
    String baseTopic;
    LockState lockState;
    unsigned long lastStatusTime;
    const unsigned long statusInterval = 30000; // 30초
    
    void connect();
    void subscribe();
    void callback(char* topic, byte* payload, unsigned int length);
    void handleAuthResponse(const String& payload);
    void handleCommand(const String& payload);
};

extern MQTTManager mqttManager;
```

## 구현

```cpp
#include "MQTTManager.h"
#include <ArduinoJson.h>

MQTTManager mqttManager;
WiFiClient ethClient;  // 또는 EthernetClient

void MQTTManager::begin() {
    baseTopic = "door/" + configManager.getConfig().roomCode;
    
    mqttClient.setClient(ethClient);
    mqttClient.setServer(
        configManager.getConfig().mqttServer.c_str(),
        configManager.getConfig().mqttPort
    );
    mqttClient.setCallback([this](char* t, byte* p, unsigned int l) {
        this->callback(t, p, l);
    });
    
    connect();
}

void MQTTManager::connect() {
    if (!networkManager.isConnected()) {
        return;
    }
    
    String clientId = "DoorDot-" + configManager.getConfig().roomCode;
    
    if (mqttClient.connect(clientId.c_str())) {
        Serial.println("MQTT connected");
        subscribe();
        publishStatus();
    } else {
        Serial.print("MQTT failed, rc=");
        Serial.println(mqttClient.state());
    }
}

void MQTTManager::subscribe() {
    mqttClient.subscribe((baseTopic + "/command").c_str());
    mqttClient.subscribe((baseTopic + "/auth/response").c_str());
}

void MQTTManager::update() {
    if (!mqttClient.connected() && networkManager.isConnected()) {
        connect();
    }
    
    mqttClient.loop();
    
    // 주기적 상태 발행
    if (millis() - lastStatusTime > statusInterval) {
        publishStatus();
        lastStatusTime = millis();
    }
}

bool MQTTManager::isConnected() {
    return mqttClient.connected();
}
```

## 상태 발행

```cpp
void MQTTManager::publishStatus() {
    StaticJsonDocument<256> doc;
    
    doc["timestamp"] = millis();
    doc["connected"] = true;
    doc["lock_state"] = (lockState == LockState::CLOSED) ? "closed" : "opened";
    doc["network"] = networkManager.getType() == NetworkType::ETHERNET ? "ethernet" : "wifi";
    doc["ip"] = networkManager.getIP();
    
    char buffer[256];
    serializeJson(doc, buffer);
    
    mqttClient.publish((baseTopic + "/status").c_str(), buffer, true);
}

void MQTTManager::publishLockState(LockState state) {
    lockState = state;
    publishStatus();
}

void MQTTManager::publishEvent(const String& eventType, const String& data) {
    StaticJsonDocument<256> doc;
    
    doc["type"] = eventType;
    doc["data"] = data;
    doc["timestamp"] = millis();
    
    char buffer[256];
    serializeJson(doc, buffer);
    
    mqttClient.publish((baseTopic + "/event").c_str(), buffer, false);
}
```

## 인증 요청

```cpp
bool MQTTManager::requestAuth(const String& qrCode, AuthResult& result) {
    StaticJsonDocument<128> doc;
    
    doc["action"] = "auth_request";
    doc["qr_code"] = qrCode;
    doc["timestamp"] = millis();
    
    char buffer[128];
    serializeJson(doc, buffer);
    
    return mqttClient.publish((baseTopic + "/auth/request").c_str(), buffer);
}
```

## 콜백 처리

```cpp
void MQTTManager::callback(char* topic, byte* payload, unsigned int length) {
    String topicStr = String(topic);
    String payloadStr;
    payloadStr.reserve(length);
    for (unsigned int i = 0; i < length; i++) {
        payloadStr += (char)payload[i];
    }
    
    if (topicStr.endsWith("/auth/response")) {
        handleAuthResponse(payloadStr);
    } else if (topicStr.endsWith("/command")) {
        handleCommand(payloadStr);
    }
}

void MQTTManager::handleAuthResponse(const String& payload) {
    StaticJsonDocument<256> doc;
    deserializeJson(doc, payload);
    
    AuthResult result;
    result.success = doc["success"];
    result.userName = doc["user_name"].as<String>();
    result.openDuration = doc["open_duration"] | 5;
    
    if (onAuthCallback) {
        onAuthCallback(result);
    }
}

void MQTTManager::handleCommand(const String& payload) {
    StaticJsonDocument<128> doc;
    deserializeJson(doc, payload);
    
    String command = doc["command"];
    
    if (onCommandCallback) {
        onCommandCallback(command);
    }
}
```

## main.cpp 통합

```cpp
#include "MQTTManager.h"

void onAuthResult(AuthResult result) {
    if (result.success) {
        uiManager.showScreen(Screen::OPENED);
        uiManager.setUserName(result.userName);
        emlockManager.open(result.openDuration * 1000);
        mqttManager.publishEvent("door_open", result.userName);
    } else {
        uiManager.showError("인증 실패");
    }
}

void onCommand(String command) {
    if (command == "open") {
        emlockManager.open(5000);
    } else if (command == "close") {
        emlockManager.close();
    }
}

void setup() {
    // ...
    mqttManager.begin();
    mqttManager.setOnAuthCallback(onAuthResult);
    mqttManager.setOnCommandCallback(onCommand);
}

void loop() {
    // ...
    mqttManager.update();
    uiManager.setMQTTStatus(mqttManager.isConnected());
}
```

## platformio.ini 라이브러리 추가

```ini
lib_deps =
    https://github.com/bssm-oss/NanoUI.git
    Ethernet
    PubSubClient
    ArduinoJson
```

## 파일 구조

```
src/
├── mqtt/
│   ├── MQTTManager.h
│   └── MQTTManager.cpp
└── main.cpp
```

## Keep-Alive 설정

```cpp
mqttClient.setKeepAlive(60);  // 60초
mqttClient.setSocketTimeout(30);  // 30초
```

## Last Will (LWT) 설정

장치가 비정상 종료 시 자동으로 오프라인 상태 발행:

```cpp
bool MQTTManager::connect() {
    String clientId = "DoorDot-" + configManager.getConfig().roomCode;
    String willTopic = baseTopic + "/status";
    
    StaticJsonDocument<128> willDoc;
    willDoc["connected"] = false;
    willDoc["timestamp"] = 0;
    
    char willPayload[128];
    serializeJson(willDoc, willPayload);
    
    return mqttClient.connect(
        clientId.c_str(),
        NULL, NULL,           // username, password
        willTopic.c_str(),
        1,                    // QoS
        true,                 // retain
        willPayload
    );
}
```