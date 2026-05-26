#pragma once

#include "tasks/TaskBase.h"
#include "core/Queues.h"
#include "ui/UIManager.h"
#include "lock/EMLockManager.h"
#include "network/MQTTClient.h"
#include "scanner/QRScanner.h"

class StateManagerTask : public TaskBase {
public:
    StateManagerTask()
        : TaskBase("StateManagerTask", STATE_TASK_STACK, 5, 1) {}

    SystemState getState() const { return currentState; }

protected:
    void run() override {
        currentState = SystemState::UNREGISTERED;

        // 초기 상태 설정
        if (configManager.isRegistered()) {
            currentState = SystemState::REGISTERED;
            Queues::toRender(makeStateEvent(SystemState::UNREGISTERED, currentState));
        } else {
            Queues::toRender(makeStateEvent(SystemState::UNREGISTERED, currentState));
        }

        while (running) {
            Event e;
            if (Queues::recv(Queues::eventQueue, e)) {
                handleEvent(e);
            }
        }
    }

private:
    SystemState currentState;

    void handleEvent(const Event& e) {
        Serial.printf("[STATE] Event: type=%d, state=%s\n", (int)e.type, stateName(currentState));

        switch (e.type) {
            case EventType::QR_SCANNED:
                handleQR(e);
                break;

            case EventType::AUTH_SUCCESS:
                handleAuthSuccess(e);
                break;

            case EventType::AUTH_FAILED:
                handleAuthFailed();
                break;

            case EventType::COMMAND_RECEIVED:
                handleCommand(e);
                break;

            case EventType::MQTT_LINKED:
                if (currentState == SystemState::REGISTERED) {
                    transitionTo(SystemState::READY);
                }
                break;

            case EventType::MQTT_LOST:
                if (currentState == SystemState::READY) {
                    // 연결 끊김은 에러 화면 대신 상태만 표시
                }
                break;

            case EventType::NETWORK_CONNECTED:
                // 네트워크 연결 -> MQTT 연결 시도 (NetworkTask에서 처리)
                break;

            case EventType::REGISTRATION_REQUEST:
                handleRegistration(e);
                break;

            default:
                break;
        }
    }

    void handleQR(const Event& e) {
        QRType qrType = e.data.qr.qrType;

        if (qrType == QRType::ROOM_CODE) {
            // 정독실 등록
            if (!configManager.isRegistered()) {
                configManager.setRoomCode(e.data.qr.code);
                configManager.save();

                Queues::toRender(makeStateEvent(currentState, SystemState::REGISTERED));
                currentState = SystemState::REGISTERED;

                // 2초 후 재부팅
                delayMs(2000);
                ESP.restart();
            } else {
                Queues::toRender(makeErrorEvent("Already registered", 0));
            }
        } else if (qrType == QRType::USER_CODE) {
            // 사용자 인증
            if (currentState == SystemState::READY && mqttClient.isConnected()) {
                transitionTo(SystemState::AUTHENTICATING);
                mqttClient.publishAuthRequest(e.data.qr.code);
            } else if (currentState != SystemState::READY) {
                Queues::toRender(makeErrorEvent("Scan unavailable", 0));
            } else {
                Queues::toRender(makeErrorEvent("No network", 0));
            }
        } else {
            Queues::toRender(makeErrorEvent("Unknown QR", 0));
        }
    }

    void handleAuthSuccess(const Event& e) {
        if (currentState != SystemState::AUTHENTICATING) return;

        const char* userName = e.data.auth.userName;
        uint16_t duration = e.data.auth.duration;

        // 문 열기
        emlockManager.open(duration * 1000);
        transitionTo(SystemState::OPENED);

        // UI 업데이트
        Queues::toRender(makeTimerEvent(duration, duration));

        // 이벤트 발행
        mqttClient.publishEvent("door_open", userName);
        mqttClient.publishStatus(LockState::UNLOCKED);
    }

    void handleAuthFailed() {
        if (currentState != SystemState::AUTHENTICATING) return;

        Queues::toRender(makeErrorEvent("Auth failed", 0));
        transitionTo(SystemState::ERROR);

        // 3초 후 복귀
        delayMs(3000);
        if (mqttClient.isConnected()) {
            transitionTo(SystemState::READY);
        } else {
            transitionTo(SystemState::REGISTERED);
        }
    }

    void handleCommand(const Event& e) {
        const char* cmd = e.data.cmd.command;

        if (strcmp(cmd, "open") == 0) {
            if (currentState == SystemState::READY) {
                emlockManager.open(e.data.cmd.param > 0 ? e.data.cmd.param * 1000 : DEFAULT_OPEN_DURATION_MS);
                transitionTo(SystemState::OPENED);
                mqttClient.publishStatus(LockState::UNLOCKED);
            }
        } else if (strcmp(cmd, "close") == 0) {
            if (currentState == SystemState::OPENED) {
                emlockManager.close();
                transitionTo(SystemState::READY);
                mqttClient.publishStatus(LockState::LOCKED);
                mqttClient.publishEvent("door_close", "command");
            }
        }
    }

    void handleRegistration(const Event& e) {
        // 이미 QR_SCANNED에서 처리됨
    }

    void transitionTo(SystemState newState) {
        SystemState oldState = currentState;
        currentState = newState;

        Queues::toRender(makeStateEvent(oldState, newState));
        Serial.printf("[STATE] Transition: %s -> %s\n", stateName(oldState), stateName(newState));
    }
};

extern StateManagerTask stateManagerTask;