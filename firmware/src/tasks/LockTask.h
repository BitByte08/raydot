#pragma once

#include "tasks/TaskBase.h"
#include "core/Queues.h"
#include "lock/EMLockManager.h"

class LockTask : public TaskBase {
public:
    LockTask()
        : TaskBase("LockTask", LOCK_TASK_STACK, 4, 1) {}

protected:
    void run() override {
        TickType_t lastWake = xTaskGetTickCount();
        const TickType_t interval = pdMS_TO_TICKS(100);

        unsigned long lastTimerSent = 0;

        while (running) {
            emlockManager.update();

            // 타이머 진행 중이면 UI 업데이트
            if (emlockManager.isOpen()) {
                if (millis() - lastTimerSent > 500) {  // 0.5초마다 업데이트
                    uint16_t remaining = emlockManager.getRemainingMs() / 1000;
                    uint16_t total = emlockManager.getDurationMs() / 1000;
                    Queues::toRender(makeTimerEvent(remaining, total));
                    lastTimerSent = millis();
                }
            }

            vTaskDelayUntil(&lastWake, interval);
        }
    }
};

extern LockTask lockTask;