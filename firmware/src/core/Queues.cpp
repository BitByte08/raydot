#include "Queues.h"

QueueHandle_t Queues::eventQueue   = nullptr;
QueueHandle_t Queues::renderQueue  = nullptr;
QueueHandle_t Queues::networkQueue = nullptr;

SemaphoreHandle_t Mutexes::uiMutex     = nullptr;
SemaphoreHandle_t Mutexes::configMutex = nullptr;

void Queues::init() {
    eventQueue   = xQueueCreate(EVENT_QUEUE_SIZE, sizeof(Event));
    renderQueue  = xQueueCreate(RENDER_QUEUE_SIZE, sizeof(Event));
    networkQueue = xQueueCreate(NETWORK_QUEUE_SIZE, sizeof(Event));
    configASSERT(eventQueue);
    configASSERT(renderQueue);
    configASSERT(networkQueue);
}

void Mutexes::init() {
    uiMutex     = xSemaphoreCreateMutex();
    configMutex = xSemaphoreCreateMutex();
    configASSERT(uiMutex);
    configASSERT(configMutex);
}
