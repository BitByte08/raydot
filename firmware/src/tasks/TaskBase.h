#pragma once

#include <Arduino.h>
#include <freertos/FreeRTOS.h>
#include <freertos/task.h>

class TaskBase {
public:
    TaskBase(const char* name, uint32_t stackSize, UBaseType_t priority, BaseType_t core = tskNO_AFFINITY);
    virtual ~TaskBase() = default;

    void start();
    void stop();

    TaskHandle_t getHandle() const { return taskHandle; }
    const char*  getName()   const { return taskName; }
    bool         isRunning() const { return running; }

protected:
    virtual void run() = 0;

    void delayMs(uint32_t ms) { vTaskDelay(pdMS_TO_TICKS(ms)); }

    const char*   taskName;
    uint32_t      stackSize;
    UBaseType_t   priority;
    BaseType_t    coreId;
    TaskHandle_t  taskHandle = nullptr;
    bool          running = false;

private:
    static void taskEntry(void* param);
};
