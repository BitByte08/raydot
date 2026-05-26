#pragma once

#include "tasks/TaskBase.h"
#include "core/Queues.h"
#include "ui/UIManager.h"
#include "network/NetworkManager.h"

class RenderTask : public TaskBase {
public:
    RenderTask()
        : TaskBase("RenderTask", RENDER_TASK_STACK, 2, 0) {}

protected:
    void run() override {
        TickType_t lastWake = xTaskGetTickCount();
        const TickType_t interval = pdMS_TO_TICKS(RENDER_INTERVAL_MS);

        while (running) {
            // UI 업데이트
            uiManager.update();

            // 이벤트 처리
            Event e;
            if (Queues::recv(Queues::renderQueue, e, 0)) {
                handleEvent(e);
            }

            vTaskDelayUntil(&lastWake, interval);
        }
    }

    void handleEvent(const Event& e) {
        switch (e.type) {
            case EventType::STATE_CHANGE:
                handleStateChange(e.data.state.newState);
                break;

            case EventType::LOCK_TIMER_UPDATE:
                uiManager.setOpenTimer(e.data.timer.remaining, e.data.timer.total);
                break;

            case EventType::MQTT_LINKED:
                uiManager.setMQTTStatus(true);
                break;

            case EventType::MQTT_LOST:
                uiManager.setMQTTStatus(false);
                break;

            case EventType::NETWORK_CONNECTED:
                uiManager.setNetworkStatus(true);
                break;

            case EventType::NETWORK_DISCONNECTED:
                uiManager.setNetworkStatus(false);
                break;

            case EventType::ERROR_OCCURRED:
                uiManager.setErrorMsg(e.data.error.message);
                uiManager.showScreen(Screen::ERROR);
                break;

            default:
                break;
        }
    }

    void handleStateChange(SystemState state) {
        switch (state) {
            case SystemState::UNREGISTERED:
                if (networkManager.isInAPMode()) {
                    uiManager.showScreen(Screen::WIFI_SETUP);
                    uiManager.setAPName(networkManager.getAPName());
                } else {
                    uiManager.showScreen(Screen::REGISTRATION);
                }
                break;
            case SystemState::REGISTERED:
                uiManager.showScreen(Screen::REGISTERED);
                break;
            case SystemState::READY:
                uiManager.showScreen(Screen::CLOSED);
                uiManager.setRoomCode(configManager.getConfig().roomCode);
                break;
            case SystemState::OPENED:
                uiManager.showScreen(Screen::OPENED);
                break;
            case SystemState::ERROR:
                uiManager.showScreen(Screen::ERROR);
                break;
            default:
                break;
        }
    }
};

extern RenderTask renderTask;