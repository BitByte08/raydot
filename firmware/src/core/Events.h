#pragma once

#include <Arduino.h>
#include <freertos/FreeRTOS.h>
#include <freertos/queue.h>

// ── 시스템 상태 ──────────────────────────────────────────
enum class SystemState : uint8_t {
    UNREGISTERED,
    REGISTERING,
    REGISTERED,
    NETWORK_CONNECTING,
    READY,
    AUTHENTICATING,
    OPENED,
    ERROR
};

// ── 이벤트 타입 ──────────────────────────────────────────
enum class EventType : uint8_t {
    QR_SCANNED,
    NETWORK_CONNECTED,
    NETWORK_DISCONNECTED,
    MQTT_LINKED,
    MQTT_LOST,
    AUTH_SUCCESS,
    AUTH_FAILED,
    COMMAND_RECEIVED,
    LOCK_OPENED,
    LOCK_CLOSED,
    LOCK_TIMER_UPDATE,
    REGISTRATION_REQUEST,
    REGISTRATION_SUCCESS,
    REGISTRATION_FAILED,
    STATE_CHANGE,
    ERROR_OCCURRED,
};

// ── QR 타입 ──────────────────────────────────────────────
enum class QRType : uint8_t {
    ROOM_CODE,
    USER_CODE,
    UNKNOWN
};

// ── 잠금 상태 ────────────────────────────────────────────
enum class LockState : uint8_t {
    LOCKED,
    UNLOCKED
};

// ── 네트워크 타입 ────────────────────────────────────────
enum class NetworkType : uint8_t {
    ETHERNET,
    WIFI,
    NONE
};

// ── 이벤트 구조체 ────────────────────────────────────────
struct Event {
    EventType type;
    uint32_t  timestamp;

    union {
        struct { char code[64]; QRType qrType; } qr;
        struct { char userName[32]; uint16_t duration; } auth;
        struct { char command[16]; int16_t param; } cmd;
        struct { uint16_t remaining; uint16_t total; } timer;
        struct { char roomCode[32]; } registration;
        struct { SystemState newState; SystemState oldState; } state;
        struct { char message[48]; int16_t code; } error;
    } data;
};

// ── 이벤트 빌더 ──────────────────────────────────────────
inline Event makeEvent(EventType type) {
    Event e{}; e.type = type; e.timestamp = millis(); return e;
}

inline Event makeQREvent(const char* code, QRType qrType) {
    Event e = makeEvent(EventType::QR_SCANNED);
    strncpy(e.data.qr.code, code, sizeof(e.data.qr.code) - 1);
    e.data.qr.qrType = qrType;
    return e;
}

inline Event makeAuthSuccessEvent(const char* name, uint16_t dur) {
    Event e = makeEvent(EventType::AUTH_SUCCESS);
    strncpy(e.data.auth.userName, name, sizeof(e.data.auth.userName) - 1);
    e.data.auth.duration = dur;
    return e;
}

inline Event makeAuthFailedEvent() {
    return makeEvent(EventType::AUTH_FAILED);
}

inline Event makeCommandEvent(const char* cmd, int16_t param = 0) {
    Event e = makeEvent(EventType::COMMAND_RECEIVED);
    strncpy(e.data.cmd.command, cmd, sizeof(e.data.cmd.command) - 1);
    e.data.cmd.param = param;
    return e;
}

inline Event makeTimerEvent(uint16_t remaining, uint16_t total) {
    Event e = makeEvent(EventType::LOCK_TIMER_UPDATE);
    e.data.timer.remaining = remaining;
    e.data.timer.total = total;
    return e;
}

inline Event makeStateEvent(SystemState from, SystemState to) {
    Event e = makeEvent(EventType::STATE_CHANGE);
    e.data.state.oldState = from;
    e.data.state.newState = to;
    return e;
}

inline Event makeErrorEvent(const char* msg, int16_t code = 0) {
    Event e = makeEvent(EventType::ERROR_OCCURRED);
    strncpy(e.data.error.message, msg, sizeof(e.data.error.message) - 1);
    e.data.error.code = code;
    return e;
}

inline Event makeNetworkEvent(bool connected) {
    return makeEvent(connected ? EventType::NETWORK_CONNECTED
                               : EventType::NETWORK_DISCONNECTED);
}

inline Event makeMQTTEvent(bool connected) {
    return makeEvent(connected ? EventType::MQTT_LINKED
                               : EventType::MQTT_LOST);
}

// ── 상태 이름 문자열 ─────────────────────────────────────
inline const char* stateName(SystemState s) {
    switch (s) {
        case SystemState::UNREGISTERED:       return "UNREGISTERED";
        case SystemState::REGISTERING:        return "REGISTERING";
        case SystemState::REGISTERED:         return "REGISTERED";
        case SystemState::NETWORK_CONNECTING: return "NET_CONNECTING";
        case SystemState::READY:              return "READY";
        case SystemState::AUTHENTICATING:     return "AUTH";
        case SystemState::OPENED:             return "OPENED";
        case SystemState::ERROR:              return "ERROR";
        default: return "???";
    }
}
