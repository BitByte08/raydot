#pragma once

#include <Arduino.h>
#include <freertos/FreeRTOS.h>
#include <freertos/queue.h>
#include <freertos/semphr.h>
#include "core/Events.h"
#include "config/pins.h"

namespace Queues {
    extern QueueHandle_t eventQueue;
    extern QueueHandle_t renderQueue;
    extern QueueHandle_t networkQueue;

    void init();

    inline bool send(QueueHandle_t q, const Event& e, uint32_t ms = 100) {
        return xQueueSend(q, &e, pdMS_TO_TICKS(ms)) == pdTRUE;
    }
    inline bool recv(QueueHandle_t q, Event& e, uint32_t ms = UINT32_MAX) {
        TickType_t t = (ms == UINT32_MAX) ? portMAX_DELAY : pdMS_TO_TICKS(ms);
        return xQueueReceive(q, &e, t) == pdTRUE;
    }
    inline bool toState(const Event& e)   { return send(eventQueue, e); }
    inline bool toRender(const Event& e)  { return send(renderQueue, e); }
    inline bool toNetwork(const Event& e) { return send(networkQueue, e); }
}

namespace Mutexes {
    extern SemaphoreHandle_t uiMutex;
    extern SemaphoreHandle_t configMutex;

    void init();

    class Lock {
    public:
        explicit Lock(SemaphoreHandle_t m, uint32_t ms = 1000) : mtx(m), ok(xSemaphoreTake(m, pdMS_TO_TICKS(ms)) == pdTRUE) {}
        ~Lock() { if (ok) xSemaphoreGive(mtx); }
        bool acquired() const { return ok; }
    private:
        SemaphoreHandle_t mtx;
        bool ok;
    };
}
