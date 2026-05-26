#include <Arduino.h>

#include "config/ConfigManager.h"
#include "config/pins.h"

#include "core/Queues.h"
#include "core/Events.h"

#include "ui/UIManager.h"

#include "network/NetworkManager.h"
#include "network/MQTTClient.h"

#include "scanner/QRScanner.h"

#include "lock/EMLockManager.h"

#include "tasks/TaskBase.h"
#include "tasks/RenderTask.h"
#include "tasks/NetworkTask.h"
#include "tasks/QRScannerTask.h"
#include "tasks/LockTask.h"
#include "tasks/StateManagerTask.h"

// ── 태스크 인스턴스 ──────────────────────────────────────────
RenderTask       renderTask;
NetworkTask      networkTask;
QRScannerTask    qrScannerTask;
LockTask         lockTask;
StateManagerTask stateManagerTask;

// ── Reset Switch 처리 ───────────────────────────────────────
// DISABLED: GPIO 39는 input-only이며 내부 pull-up이 없음.
// 외부 10kΩ pull-up resistor를 GPIO 39에 추가한 후 이 코드를 활성화하세요.
void checkResetSwitch() {
    // Reset 기능 비활성화
    Serial.println("[RESET] Feature disabled (external pull-up required on GPIO 39)");
    return;
    
    // 외부 pull-up 설치 후 활성화:
    // pinMode(RESET_PIN, INPUT);
    // if (digitalRead(RESET_PIN) == LOW) {
    //     delay(5000);
    //     if (digitalRead(RESET_PIN) == LOW) {
    //         Serial.println("[RESET] Clearing all config...");
    //         configManager.clear();
    //         delay(1000);
    //         ESP.restart();
    //     }
    // }
}

// ── 초기화 ────────────────────────────────────────────────────
void setup() {
    Serial.begin(115200);
    Serial.println("\n[Door.dot] System starting...");

    // Reset Switch 체크 (GPIO 39: input-only, pullup 없음 → 외부 pullup 필요)
    checkResetSwitch();

    // 1. Config 로드
    configManager.begin();
    Serial.printf("[CONFIG] Registered: %s\n",
                  configManager.isRegistered() ? configManager.getConfig().roomCode : "NO");

    // 2. Queue & Mutex 초기화
    Queues::init();
    Mutexes::init();

    // 3. 하드웨어 모듈 초기화
    uiManager.begin();
    networkManager.begin();
    mqttClient.begin();
    qrScanner.begin();
    emlockManager.begin();

    // 4. FreeRTOS 태스크 시작
    Serial.println("[RTOS] Starting tasks...");

    renderTask.start();       // Core 0 (UI)
    networkTask.start();      // Core 1
    qrScannerTask.start();    // Core 1
    lockTask.start();         // Core 1
    stateManagerTask.start(); // Core 1

    Serial.println("[Door.dot] System ready!");
}

// ── 루프 (FreeRTOS 태스크가 실행되므로 최소화) ──────────────────
void loop() {
    // FreeRTOS 태스크가 모든 작업을 처리
    delay(1000);
}