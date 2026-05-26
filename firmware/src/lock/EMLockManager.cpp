#include "EMLockManager.h"
#include "config/pins.h"

EMLockManager& EMLockManager::getInstance() {
    static EMLockManager instance;
    return instance;
}

EMLockManager& emlockManager = EMLockManager::getInstance();

void EMLockManager::begin() {
    pinMode(pin, OUTPUT);
    setHardware(true);  // 초기 상태: 잠금
    state = LockState::LOCKED;
    timerActive = false;
    Serial.println("[LOCK] EMLock initialized (LOCKED)");
}

void EMLockManager::open(unsigned long durationMs) {
    setHardware(false);  // 열림
    state = LockState::UNLOCKED;
    openStartTime = millis();
    openDuration = durationMs;
    timerActive = true;
    Serial.printf("[LOCK] Opened for %lu ms\n", durationMs);
}

void EMLockManager::close() {
    setHardware(true);  // 잠금
    state = LockState::LOCKED;
    timerActive = false;
    Serial.println("[LOCK] Closed");
}

void EMLockManager::update() {
    if (timerActive && state == LockState::UNLOCKED) {
        if (millis() - openStartTime >= openDuration) {
            close();
        }
    }
}

unsigned long EMLockManager::getRemainingMs() const {
    if (!timerActive || state == LockState::LOCKED) return 0;
    unsigned long elapsed = millis() - openStartTime;
    return (elapsed >= openDuration) ? 0 : (openDuration - elapsed);
}

void EMLockManager::setHardware(bool locked) {
    // Active Low: HIGH = 잠금 (릴레이 OFF), LOW = 열림 (릴레이 ON)
    if (activeLow) {
        digitalWrite(pin, locked ? HIGH : LOW);
    } else {
        digitalWrite(pin, locked ? LOW : HIGH);
    }
}
