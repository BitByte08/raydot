#pragma once

#include <Arduino.h>

// LCD (NanoUI 8-bit Parallel 모드)
// 보드 variants에서 이미 정의될 수 있으므로 undef
#ifdef TFT_CS
#undef TFT_CS
#endif
#ifdef TFT_DC
#undef TFT_DC
#endif

#define TFT_CS      27
#define TFT_DC       2
#define TFT_WR       4
#define TFT_RST     33
#define TOUCH_CS     5

#define TFT_DB0     12
#define TFT_DB1     13
#define TFT_DB2     14
#define TFT_DB3     15
#define TFT_DB4     21
#define TFT_DB5     22
#define TFT_DB6     25
#define TFT_DB7     26

// Touch SPI bus (XPT2046)
#define TOUCH_SCK   18
#define TOUCH_MISO  19
#define TOUCH_MOSI  23

// QR 스캐너 (UART)
// GPIO 16/17은 PSRAM과 충돌 → GPIO 34 (input-only)를 RX로 사용
#define QR_RX_PIN   34  // Input-only, PSRAM-safe
#define QR_TX_PIN   -1  // TX 사용 안 함 (QR 스캐너는 데이터만 받음)

// EMLock (Relay)
#define LOCK_PIN    32
#define LOCK_ACTIVE_LOW true

// Reset Switch (input-only GPIO 사용)
#define RESET_PIN   39  // GPIO 39: input-only, boot safe

// 내장 LED (TFT_DC=2와 충돌 방지, LED 사용 안 함)
// #define LED_PIN     2  // DISABLED: conflicts with TFT_DC

// QR 속도 제한
#define QR_MIN_INTERVAL_MS 2000

// EMLock 기본 열림 시간
#define DEFAULT_OPEN_DURATION_MS 5000

// MQTT 상태 발행 주기
#define MQTT_STATUS_INTERVAL_MS 30000

// 렌더 FPS
#define RENDER_INTERVAL_MS 33

// Queue 크기
#define EVENT_QUEUE_SIZE   10
#define RENDER_QUEUE_SIZE  16
#define NETWORK_QUEUE_SIZE 8

// 태스크 스택 크기
#define STATE_TASK_STACK   8192
#define RENDER_TASK_STACK  16384
#define NETWORK_TASK_STACK 8192
#define QR_TASK_STACK      4096
#define LOCK_TASK_STACK    4096
