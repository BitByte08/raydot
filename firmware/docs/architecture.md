# Door.dot 시스템 아키텍처 (FreeRTOS)

## 개요

ESP32 기반 정독실 출입 제어 시스템. 
**FreeRTOS 멀티태스킹 + Queue 기반 메시지 전달**로 렌더링과 연산 분리.

## FreeRTOS 태스크 구조

```
┌─────────────────────────────────────────────────────────────┐
│                        ESP32 (FreeRTOS)                      │
│                                                              │
│  ┌────────────────┐     Queue      ┌────────────────┐       │
│  │  NetworkTask   │ ─────────────→ │  StateManager  │       │
│  │  (WiFi/MQTT)   │                │   (Core Logic) │       │
│  └────────────────┘                └───────┬────────┘       │
│         ↑                                  │                 │
│         │ Queue                            │ Queue           │
│  ┌──────┴─────────┐                        ↓                 │
│  │   QRScanner    │                ┌────────────────┐       │
│  │     Task       │ ─────────────→ │   RenderTask   │       │
│  └────────────────┘                │    (LCD/UI)    │       │
│                                    └────────────────┘       │
│         ↑                                  ↑                 │
│         │ Queue                            │ Queue           │
│  ┌──────┴─────────┐                        │                 │
│  │   LockTask     │ ───────────────────────┘                 │
│  │   (EMLock)     │                                          │
│  └────────────────┘                                          │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## 태스크 정의

| 태스크 | 코어 | 우선순위 | 스택 | 주기 |
|--------|------|----------|------|------|
| StateManager | 1 | HIGH | 8KB | Event-driven |
| RenderTask | 0 | NORMAL | 16KB | 30 FPS |
| NetworkTask | 1 | NORMAL | 8KB | Event-driven |
| QRScannerTask | 1 | NORMAL | 4KB | Event-driven |
| LockTask | 1 | HIGH | 4KB | Event-driven |

## Queue 구조

```cpp
// 이벤트 타입 정의
enum class EventType {
    // QR 관련
    QR_SCANNED,
    
    // 네트워크 관련
    NETWORK_CONNECTED,
    NETWORK_DISCONNECTED,
    MQTT_CONNECTED,
    MQTT_DISCONNECTED,
    AUTH_SUCCESS,
    AUTH_FAILED,
    COMMAND_RECEIVED,
    
    // 잠금 관련
    LOCK_OPENED,
    LOCK_CLOSED,
    LOCK_TIMER_UPDATE,
    
    // 시스템
    REGISTRATION_COMPLETE,
    ERROR_OCCURRED,
    STATE_CHANGE
};

// 이벤트 데이터
struct Event {
    EventType type;
    union {
        struct {
            char qrCode[64];
            int qrType;
        } qr;
        
        struct {
            char userName[32];
            int duration;
        } auth;
        
        struct {
            char command[16];
        } cmd;
        
        struct {
            int remainingSeconds;
            int totalSeconds;
        } timer;
        
        struct {
            char roomCode[32];
        } registration;
        
        struct {
            char message[64];
            int errorCode;
        } error;
        
        struct {
            int newState;
        } state;
    } data;
};

// Queue 핸들
QueueHandle_t eventQueue;      // StateManager용
QueueHandle_t renderQueue;     // RenderTask용
```

## 클래스 다이어그램

```
┌─────────────────────────────────────────────────────────────┐
│                        StateManager                          │
│  - currentState: SystemState                                 │
│  - eventQueue: QueueHandle                                   │
│  + begin()                                                   │
│  + processEvent(Event)                                       │
│  + getState(): SystemState                                   │
└───────────────────────────┬─────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌───────────────┐  ┌───────────────┐  ┌───────────────┐
│  QRScanner    │  │ NetworkManager│  │ EMLockManager │
│  (Task)       │  │   (Task)      │  │   (Task)      │
│---------------│  │---------------│  │---------------│
│ - serial      │  │ - wifiClient  │  │ - pin         │
│ - minInterval │  │ - mqttClient  │  │ - state       │
│ + begin()     │  │ + begin()     │  │ + begin()     │
│ + update()    │  │ + update()    │  │ + open(ms)    │
│ + scan()      │  │ + connect()   │  │ + close()     │
└───────┬───────┘  └───────┬───────┘  └───────┬───────┘
        │                  │                  │
        │ eventQueue       │ eventQueue       │ eventQueue
        └──────────────────┴──────────────────┘
                            │
                            ▼
                    ┌───────────────┐
                    │  RenderTask   │
                    │  (UIManager)  │
                    │---------------│
                    │ - ui: NanoUI  │
                    │ - renderQueue │
                    │ + begin()     │
                    │ + render()    │
                    │ + showScreen()│
                    └───────────────┘
```

## 파일 구조

```
src/
├── config/
│   ├── ConfigManager.h
│   ├── ConfigManager.cpp
│   └── pins.h
│
├── core/
│   ├── StateManager.h
│   ├── StateManager.cpp
│   ├── Events.h
│   └── SystemState.h
│
├── tasks/
│   ├── TaskBase.h
│   ├── RenderTask.h
│   ├── RenderTask.cpp
│   ├── NetworkTask.h
│   ├── NetworkTask.cpp
│   ├── QRScannerTask.h
│   ├── QRScannerTask.cpp
│   ├── LockTask.h
│   └── LockTask.cpp
│
├── ui/
│   ├── UIManager.h
│   ├── UIManager.cpp
│   └── screens.h
│
├── network/
│   ├── NetworkManager.h
│   ├── NetworkManager.cpp
│   ├── MQTTClient.h
│   └── MQTTClient.cpp
│
├── scanner/
│   ├── QRScanner.h
│   └── QRScanner.cpp
│
├── lock/
│   ├── EMLockManager.h
│   └── EMLockManager.cpp
│
└── main.cpp
```

## 상태 머신

```cpp
enum class SystemState {
    UNREGISTERED,      // 미등록
    REGISTERING,       // 등록 진행 중
    REGISTERED,        // 등록 완료
    NETWORK_CONNECTING,// 네트워크 연결 중
    READY,             // QR 대기 (문 닫힘)
    AUTHENTICATING,    // 인증 진행 중
    OPENED,            // 문 열림
    ERROR              // 에러
};
```

## 태스크 구현 패턴

```cpp
// TaskBase.h - 모든 태스크의 기본 클래스
class TaskBase {
public:
    TaskBase(const char* name, uint32_t stackSize, UBaseType_t priority, BaseType_t core);
    virtual ~TaskBase() = default;
    
    void start();
    TaskHandle_t getHandle() const { return taskHandle; }
    
protected:
    virtual void run() = 0;
    static void taskWrapper(void* param);
    
    const char* taskName;
    uint32_t stackSize;
    UBaseType_t priority;
    BaseType_t coreId;
    TaskHandle_t taskHandle;
};

// TaskBase.cpp
TaskBase::TaskBase(const char* name, uint32_t stackSize, UBaseType_t priority, BaseType_t core)
    : taskName(name), stackSize(stackSize), priority(priority), coreId(core), taskHandle(nullptr) {}

void TaskBase::start() {
    xTaskCreatePinnedToCore(
        taskWrapper,
        taskName,
        stackSize,
        this,
        priority,
        &taskHandle,
        coreId
    );
}

void TaskBase::taskWrapper(void* param) {
    TaskBase* task = static_cast<TaskBase*>(param);
    task->run();
    vTaskDelete(nullptr);
}
```

## 데이터 흐름

### QR 스캔 → 문 열림 플로우

```
1. QRScannerTask
   │ QR 스캔 감지
   ├─→ Event { QR_SCANNED, qrCode: "USER:123" }
   │   push to eventQueue
   │
2. StateManager
   │ eventQueue에서 이벤트 수신
   ├─→ 상태: READY → AUTHENTICATING
   ├─→ Event { STATE_CHANGE, newState: AUTHENTICATING }
   │   push to renderQueue
   ├─→ MQTTClient에 인증 요청
   │
3. NetworkTask (MQTT)
   │ 서버로부터 인증 응답 수신
   ├─→ Event { AUTH_SUCCESS, userName: "홍길동", duration: 5 }
   │   push to eventQueue
   │
4. StateManager
   │ 인증 성공 이벤트 수신
   ├─→ 상태: AUTHENTICATING → OPENED
   ├─→ EMLockManager.open(5000) 호출
   ├─→ Event { STATE_CHANGE, newState: OPENED }
   │   push to renderQueue
   ├─→ Event { LOCK_OPENED }
   │   push to renderQueue
   │
5. LockTask
   │ 타이머 시작
   ├─→ 매초 Event { LOCK_TIMER_UPDATE, remainingSeconds: n }
   │   push to renderQueue
   │
6. RenderTask
   │ renderQueue에서 이벤트 수신
   ├─→ 화면 업데이트
   │   - 상태 표시
   │   - 타이머 표시
   │   - 사용자 이름 표시
   │
7. LockTask
   │ 타이머 완료
   ├─→ EMLockManager.close() 호출
   ├─→ Event { LOCK_CLOSED }
   │   push to eventQueue
   │
8. StateManager
   │ 잠금 닫힘 이벤트 수신
   ├─→ 상태: OPENED → READY
   ├─→ Event { STATE_CHANGE, newState: READY }
   │   push to renderQueue
   │
9. RenderTask
   │ QR 대기 화면 표시
```

## 동기화 메커니즘

```cpp
// Mutex (NanoUI 접근 보호)
SemaphoreHandle_t uiMutex;

// 이벤트 전송 헬퍼 함수
bool sendEvent(QueueHandle_t queue, const Event& event, TickType_t timeout = pdMS_TO_TICKS(100)) {
    return xQueueSend(queue, &event, timeout) == pdPASS;
}

// 이벤트 수신 헬퍼 함수
bool receiveEvent(QueueHandle_t queue, Event& event, TickType_t timeout = portMAX_DELAY) {
    return xQueueReceive(queue, &event, timeout) == pdPASS;
}
```

## 하드웨어 리소스

| 리소스 | 사용 태스크 | 접근 방식 |
|--------|-------------|-----------|
| SPI (LCD) | RenderTask | Mutex 보호 |
| Serial2 (QR) | QRScannerTask | 독점 |
| GPIO (Lock) | LockTask | 독점 |
| WiFi | NetworkTask | 독점 |
| NVS (Config) | 모든 태스크 | Mutex 보호 |

## 메모리 사용량 추정

| 태스크 | 스택 | 정적 할당 | 동적 할당 |
|--------|------|-----------|-----------|
| StateManager | 8KB | ~500B | ~1KB |
| RenderTask | 16KB | ~2KB (UI) | ~4KB (버퍼) |
| NetworkTask | 8KB | ~1KB | ~8KB (MQTT) |
| QRScannerTask | 4KB | ~300B | ~512B |
| LockTask | 4KB | ~100B | - |
| **합계** | **40KB** | ~4KB | ~14KB |

ESP32-WROVER (4MB PSRAM) 권장
