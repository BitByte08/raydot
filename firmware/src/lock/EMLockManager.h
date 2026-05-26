#pragma once

#include <Arduino.h>
#include "config/pins.h"
#include "core/Events.h"

class EMLockManager {
public:
    static EMLockManager& getInstance();

    void begin();
    void open(unsigned long durationMs = DEFAULT_OPEN_DURATION_MS);
    void close();
    void update();  // 타이머 체크

    LockState getState()      const { return state; }
    bool      isOpen()        const { return state == LockState::UNLOCKED; }
    unsigned long getRemainingMs() const;
    unsigned long getDurationMs()  const { return openDuration; }

private:
    EMLockManager() = default;

    int pin = LOCK_PIN;
    bool activeLow = LOCK_ACTIVE_LOW;
    LockState state = LockState::LOCKED;
    unsigned long openStartTime = 0;
    unsigned long openDuration = 0;
    bool timerActive = false;

    void setHardware(bool locked);
};

extern EMLockManager& emlockManager;
