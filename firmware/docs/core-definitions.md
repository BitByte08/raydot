# 공통 정의 (Events.h)

## 이벤트 시스템

```cpp
#pragma once
#include <Arduino.h>

// 시스템 상태
enum class SystemState {
    UNREGISTERED,       // 미등록 - 정독실 코드 대기
    REGISTERING,        // 등록 진행 중
    REGISTERED,         // 등록 완료
    NETWORK_CONNECTING, // 네트워크 연결 중
    READY,              // QR 대기 (문 닫힘)
    AUTHENTICATING,     // 인증 진행 중
    OPENED,             // 문 열림
    ERROR               // 에러
};

// 이벤트 타입
enum class EventType : uint8_t {
    // QR 스캐너
    QR_SCANNED,
    
    // 네트워크
    NETWORK_CONNECTED,
    NETWORK_DISCONNECTED,
    MQTT_CONNECTED,
    MQTT_DISCONNECTED,
    AUTH_SUCCESS,
    AUTH_FAILED,
    COMMAND_RECEIVED,
    
    // 잠금
    LOCK_OPENED,
    LOCK_CLOSED,
    LOCK_TIMER_UPDATE,
    
    // 등록
    REGISTRATION_REQUEST,
    REGISTRATION_SUCCESS,
    REGISTRATION_FAILED,
    
    // 시스템
    STATE_CHANGE,
    ERROR_OCCURRED,
    UI_UPDATE
};

// QR 코드 타입
enum class QRType : uint8_t {
    ROOM_CODE,      // ROOM:xxx
    USER_CODE,      // USER:xxx
    UNKNOWN
};

// 잠금 상태
enum class LockState : uint8_t {
    LOCKED,
    UNLOCKED
};

// 네트워크 타입
enum class NetworkType : uint8_t {
    ETHERNET,
    WIFI,
    NONE
};

// 이벤트 데이터 구조체
struct Event {
    EventType type;
    uint32_t timestamp;
    
    union {
        // QR 스캔 데이터
        struct {
            char code[64];
            QRType qrType;
        } qr;
        
        // 인증 결과
        struct {
            char userName[32];
            uint16_t duration;
        } auth;
        
        // 명령
        struct {
            char command[16];
            int16_t param;
        } cmd;
        
        // 타이머
        struct {
            uint16_t remaining;
            uint16_t total;
        } timer;
        
        // 등록
        struct {
            char roomCode[32];
        } registration;
        
        // 상태 변경
        struct {
            SystemState newState;
            SystemState oldState;
        } state;
        
        // 에러
        struct {
            char message[48];
            int16_t code;
        } error;
        
        // UI 업데이트
        struct {
            char text[32];
            char target[16];
        } ui;
    } data;
};

// 이벤트 초기화 헬퍼
inline Event createEvent(EventType type) {
    Event e;
    e.type = type;
    e.timestamp = millis();
    return e;
}

inline Event createQREvent(const char* code, QRType qrType) {
    Event e = createEvent(EventType::QR_SCANNED);
    strncpy(e.data.qr.code, code, sizeof(e.data.qr.code) - 1);
    e.data.qr.qrType = qrType;
    return e;
}

inline Event createAuthSuccessEvent(const char* userName, uint16_t duration) {
    Event e = createEvent(EventType::AUTH_SUCCESS);
    strncpy(e.data.auth.userName, userName, sizeof(e.data.auth.userName) - 1);
    e.data.auth.duration = duration;
    return e;
}

inline Event createTimerEvent(uint16_t remaining, uint16_t total) {
    Event e = createEvent(EventType::LOCK_TIMER_UPDATE);
    e.data.timer.remaining = remaining;
    e.data.timer.total = total;
    return e;
}

inline Event createErrorEvent(const char* message, int16_t code = 0) {
    Event e = createEvent(EventType::ERROR_OCCURRED);
    strncpy(e.data.error.message, message, sizeof(e.data.error.message) - 1);
    e.data.error.code = code;
    return e;
}
```

# 핀 정의 (pins.h)

```cpp
#pragma once

// LCD (NanoUI SPI 모드)
#define TFT_CS      10
#define TFT_DC      9
#define TFT_RST     8
#define TOUCH_CS    7

// QR 스캐너 (UART)
#define QR_RX_PIN   16
#define QR_TX_PIN   17

// EMLock (Relay)
#define LOCK_PIN    32
#define LOCK_ACTIVE_LOW true

// Reset Switch
#define RESET_PIN   33

// Ethernet (W5500)
#define ETH_CS      5
#define ETH_SCK     18
#define ETH_MISO    19
#define ETH_MOSI    23

// LED (상태 표시용, 선택적)
#define LED_PIN     2
```

# 시스템 상태 (SystemState.h)

```cpp
#pragma once
#include "Events.h"

class StateManager {
public:
    static StateManager& getInstance();
    
    void begin();
    void update();
    
    SystemState getState() const { return currentState; }
    bool isInState(SystemState state) const { return currentState == state; }
    
    // 상태 전이
    bool transitionTo(SystemState newState);
    
    // 상태 이름 가져오기
    const char* getStateName() const;
    static const char* getStateName(SystemState state);
    
private:
    StateManager() = default;
    
    SystemState currentState = SystemState::UNREGISTERED;
    bool transitionAllowed(SystemState from, SystemState to);
};

// 글로벌 접근
extern StateManager& stateManager;
```

# Task 기본 클래스 (TaskBase.h)

```cpp
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
    const char* getName() const { return taskName; }
    bool isRunning() const { return running; }
    
protected:
    virtual void run() = 0;
    virtual void onStop() {}
    
    // 유틸리티
    void delay(uint32_t ms) { vTaskDelay(pdMS_TO_TICKS(ms)); }
    void delayUntil(TickType_t& lastWakeTime, uint32_t ms) {
        vTaskDelayUntil(&lastWakeTime, pdMS_TO_TICKS(ms));
    }
    
    const char* taskName;
    uint32_t stackSize;
    UBaseType_t priority;
    BaseType_t coreId;
    TaskHandle_t taskHandle = nullptr;
    bool running = false;
    
private:
    static void taskEntry(void* param);
};
```

# TaskBase 구현 (TaskBase.cpp)

```cpp
#include "TaskBase.h"

TaskBase::TaskBase(const char* name, uint32_t stackSize, UBaseType_t priority, BaseType_t core)
    : taskName(name), stackSize(stackSize), priority(priority), coreId(core) {}

void TaskBase::start() {
    if (taskHandle != nullptr) return;
    
    xTaskCreatePinnedToCore(
        taskEntry,
        taskName,
        stackSize / sizeof(StackType_t),
        this,
        priority,
        &taskHandle,
        coreId
    );
}

void TaskBase::stop() {
    if (taskHandle == nullptr) return;
    
    running = false;
    onStop();
    
    vTaskDelete(taskHandle);
    taskHandle = nullptr;
}

void TaskBase::taskEntry(void* param) {
    TaskBase* task = static_cast<TaskBase*>(param);
    task->running = true;
    task->run();
    task->running = false;
    vTaskDelete(nullptr);
}
```

# Queue 관리 (Queues.h)

```cpp
#pragma once
#include <freertos/FreeRTOS.h>
#include <freertos/queue.h>
#include "Events.h"

namespace Queues {
    // Queue 핸들
    extern QueueHandle_t eventQueue;    // StateManager용 (주요 이벤트)
    extern QueueHandle_t renderQueue;   // RenderTask용 (UI 업데이트)
    extern QueueHandle_t networkQueue;  // NetworkTask용 (네트워크 명령)
    
    // Queue 크기
    constexpr size_t EVENT_QUEUE_SIZE = 10;
    constexpr size_t RENDER_QUEUE_SIZE = 16;
    constexpr size_t NETWORK_QUEUE_SIZE = 8;
    
    // 초기화
    void init();
    
    // 전송 헬퍼
    bool sendEvent(QueueHandle_t queue, const Event& event, uint32_t timeoutMs = 100);
    bool sendEventFromISR(QueueHandle_t queue, const Event& event, BaseType_t* pxHigherPriorityTaskWoken);
    
    // 수신 헬퍼
    bool receiveEvent(QueueHandle_t queue, Event& event, uint32_t timeoutMs = UINT32_MAX);
    
    // 편의 함수
    bool sendToStateManager(const Event& event);
    bool sendToRender(const Event& event);
    bool sendToNetwork(const Event& event);
}
```

# Queue 구현 (Queues.cpp)

```cpp
#include "Queues.h"

QueueHandle_t Queues::eventQueue = nullptr;
QueueHandle_t Queues::renderQueue = nullptr;
QueueHandle_t Queues::networkQueue = nullptr;

void Queues::init() {
    eventQueue = xQueueCreate(EVENT_QUEUE_SIZE, sizeof(Event));
    renderQueue = xQueueCreate(RENDER_QUEUE_SIZE, sizeof(Event));
    networkQueue = xQueueCreate(NETWORK_QUEUE_SIZE, sizeof(Event));
    
    // NULL 체크 (프로덕션에서는 에러 처리)
    configASSERT(eventQueue != nullptr);
    configASSERT(renderQueue != nullptr);
    configASSERT(networkQueue != nullptr);
}

bool Queues::sendEvent(QueueHandle_t queue, const Event& event, uint32_t timeoutMs) {
    return xQueueSend(queue, &event, pdMS_TO_TICKS(timeoutMs)) == pdTRUE;
}

bool Queues::sendEventFromISR(QueueHandle_t queue, const Event& event, BaseType_t* pxHigherPriorityTaskWoken) {
    return xQueueSendFromISR(queue, &event, pxHigherPriorityTaskWoken) == pdTRUE;
}

bool Queues::receiveEvent(QueueHandle_t queue, Event& event, uint32_t timeoutMs) {
    TickType_t timeout = (timeoutMs == UINT32_MAX) ? portMAX_DELAY : pdMS_TO_TICKS(timeoutMs);
    return xQueueReceive(queue, &event, timeout) == pdTRUE;
}

bool Queues::sendToStateManager(const Event& event) {
    return sendEvent(eventQueue, event);
}

bool Queues::sendToRender(const Event& event) {
    return sendEvent(renderQueue, event);
}

bool Queues::sendToNetwork(const Event& event) {
    return sendEvent(networkQueue, event);
}
```

# Mutex 관리 (Mutexes.h)

```cpp
#pragma once
#include <freertos/FreeRTOS.h>
#include <freertos/semphr.h>

namespace Mutexes {
    extern SemaphoreHandle_t uiMutex;      // NanoUI 접근 보호
    extern SemaphoreHandle_t configMutex;  // NVS/Config 접근 보호
    extern SemaphoreHandle_t serialMutex;  // Serial 출력 보호
    
    void init();
    
    // Scoped Lock
    class Lock {
    public:
        explicit Lock(SemaphoreHandle_t mutex, uint32_t timeoutMs = 1000);
        ~Lock();
        
        bool isAcquired() const { return acquired; }
        
    private:
        SemaphoreHandle_t mutex;
        bool acquired;
    };
}

// 편의 매크로
#define UI_LOCK() Mutexes::Lock lock(Mutexes::uiMutex)
#define CONFIG_LOCK() Mutexes::Lock lock(Mutexes::configMutex)
#define SERIAL_LOCK() Mutexes::Lock lock(Mutexes::serialMutex)
```

# Mutex 구현 (Mutexes.cpp)

```cpp
#include "Mutexes.h"

SemaphoreHandle_t Mutexes::uiMutex = nullptr;
SemaphoreHandle_t Mutexes::configMutex = nullptr;
SemaphoreHandle_t Mutexes::serialMutex = nullptr;

void Mutexes::init() {
    uiMutex = xSemaphoreCreateMutex();
    configMutex = xSemaphoreCreateMutex();
    serialMutex = xSemaphoreCreateMutex();
    
    configASSERT(uiMutex != nullptr);
    configASSERT(configMutex != nullptr);
    configASSERT(serialMutex != nullptr);
}

Mutexes::Lock::Lock(SemaphoreHandle_t mutex, uint32_t timeoutMs)
    : mutex(mutex), acquired(false) {
    acquired = xSemaphoreTake(mutex, pdMS_TO_TICKS(timeoutMs)) == pdTRUE;
}

Mutexes::Lock::~Lock() {
    if (acquired) {
        xSemaphoreGive(mutex);
    }
}
```
