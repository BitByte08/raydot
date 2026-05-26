#pragma once

#include "tasks/TaskBase.h"
#include "core/Queues.h"
#include "scanner/QRScanner.h"

class QRScannerTask : public TaskBase {
public:
    QRScannerTask()
        : TaskBase("QRScannerTask", QR_TASK_STACK, 2, 1) {}

protected:
    void run() override {
        TickType_t lastWake = xTaskGetTickCount();
        const TickType_t interval = pdMS_TO_TICKS(50);

        while (running) {
            if (qrScanner.scan()) {
                Event e = makeQREvent(qrScanner.getCode(), qrScanner.getType());
                Queues::toState(e);
                Serial.printf("[QR] Sent event: %s\n", qrScanner.getCode());
            }

            vTaskDelayUntil(&lastWake, interval);
        }
    }
};

extern QRScannerTask qrScannerTask;