#pragma once

#include "tasks/TaskBase.h"
#include "core/Queues.h"
#include "network/NetworkManager.h"
#include "network/MQTTClient.h"

class NetworkTask : public TaskBase {
public:
    NetworkTask()
        : TaskBase("NetworkTask", NETWORK_TASK_STACK, 3, 1) {}

protected:
    void run() override {
        TickType_t lastWake = xTaskGetTickCount();
        const TickType_t interval = pdMS_TO_TICKS(100);

        bool lastConnected = false;

        while (running) {
            networkManager.update();

            bool nowConnected = networkManager.isConnected();
            if (nowConnected != lastConnected) {
                Queues::toState(makeNetworkEvent(nowConnected));
                Queues::toRender(makeNetworkEvent(nowConnected));
                lastConnected = nowConnected;
            }

            mqttClient.update();

            bool mqttConn = mqttClient.isConnected();
            if (mqttConn != lastMQTTConnected) {
                Queues::toState(makeMQTTEvent(mqttConn));
                Queues::toRender(makeMQTTEvent(mqttConn));
                lastMQTTConnected = mqttConn;
            }

            vTaskDelayUntil(&lastWake, interval);
        }
    }

private:
    bool lastMQTTConnected = false;
};

extern NetworkTask networkTask;