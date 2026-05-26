#include "TaskBase.h"

TaskBase::TaskBase(const char* name, uint32_t stackSize, UBaseType_t priority, BaseType_t core)
    : taskName(name), stackSize(stackSize), priority(priority), coreId(core) {}

void TaskBase::start() {
    if (taskHandle != nullptr) return;
    xTaskCreatePinnedToCore(taskEntry, taskName,
                            stackSize / sizeof(StackType_t),
                            this, priority, &taskHandle, coreId);
}

void TaskBase::stop() {
    if (taskHandle == nullptr) return;
    running = false;
    vTaskDelete(taskHandle);
    taskHandle = nullptr;
}

void TaskBase::taskEntry(void* param) {
    TaskBase* t = static_cast<TaskBase*>(param);
    t->running = true;
    t->run();
    t->running = false;
    vTaskDelete(nullptr);
}
