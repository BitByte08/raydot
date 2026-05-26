#include "MQTTClient.h"
#include "network/NetworkManager.h"
#include "core/Queues.h"

MQTTClient& MQTTClient::getInstance() {
    static MQTTClient instance;
    return instance;
}

MQTTClient& mqttClient = MQTTClient::getInstance();

void MQTTClient::begin() {
    const DoorConfig& cfg = configManager.getConfig();

    if (!configManager.isRegistered()) {
        Serial.println("[MQTT] Skipped — not registered yet");
        return;
    }

    baseTopic = "door/";
    baseTopic += cfg.roomCode;

    mqtt.setClient(wifiClient);
    mqtt.setServer(cfg.mqttServer, cfg.mqttPort);
    mqtt.setCallback(staticCallback);
    mqtt.setKeepAlive(60);

    connect();
}

void MQTTClient::connect() {
    if (!networkManager.isConnected()) return;

    String clientId = "DoorDot-";
    clientId += configManager.getConfig().roomCode;

    String willTopic = baseTopic + "/status";
    const char* willPayload = "{\"connected\":false}";

    if (mqtt.connect(clientId.c_str(),
                     nullptr, nullptr,
                     willTopic.c_str(), 1, true, willPayload)) {
        Serial.println("[MQTT] Connected");
        subscribe();
        Queues::toState(makeMQTTEvent(true));
    } else {
        Serial.printf("[MQTT] Failed, rc=%d\n", mqtt.state());
    }
}

void MQTTClient::subscribe() {
    mqtt.subscribe((baseTopic + "/command").c_str());
    mqtt.subscribe((baseTopic + "/auth/response").c_str());
    Serial.printf("[MQTT] Subscribed to %s/*\n", baseTopic.c_str());
}

void MQTTClient::update() {
    if (!networkManager.isConnected()) return;

    if (!configManager.isRegistered()) return;

    if (!mqtt.connected()) {
        connect();
    }
    mqtt.loop();

    if (mqtt.connected() && millis() - lastStatusTime > MQTT_STATUS_INTERVAL_MS) {
        lastStatusTime = millis();
    }
}

bool MQTTClient::isConnected() {
    return mqtt.connected();
}

void MQTTClient::staticCallback(char* topic, byte* payload, unsigned int length) {
    mqttClient.handleCallback(topic, payload, length);
}

void MQTTClient::handleCallback(char* topic, byte* payload, unsigned int length) {
    String topicStr(topic);
    String payloadStr;
    payloadStr.reserve(length);
    for (unsigned int i = 0; i < length; i++) {
        payloadStr += (char)payload[i];
    }

    Serial.printf("[MQTT] %s = %s\n", topic, payloadStr.c_str());

    if (topicStr.endsWith("/auth/response")) {
        handleAuthResponse(payloadStr.c_str(), payloadStr.length());
    } else if (topicStr.endsWith("/command")) {
        handleCommand(payloadStr.c_str(), payloadStr.length());
    }
}

void MQTTClient::handleAuthResponse(const char* payload, size_t len) {
    String data(payload);

    int successPos = data.indexOf("\"success\":");
    if (successPos < 0) return;

    bool success = data.substring(successPos + 10, successPos + 14).indexOf("true") >= 0;

    if (success) {
        int namePos = data.indexOf("\"user_name\":");
        int durPos = data.indexOf("\"duration\":");

        String userName = "Unknown";
        int duration = 5;

        if (namePos >= 0) {
            int nameStart = data.indexOf("\"", namePos + 12) + 1;
            int nameEnd = data.indexOf("\"", nameStart);
            if (nameStart > 0 && nameEnd > nameStart) {
                userName = data.substring(nameStart, nameEnd);
            }
        }

        if (durPos >= 0) {
            int durStart = durPos + 11;
            int durEnd = data.indexOf("}", durStart);
            if (durEnd < 0) durEnd = data.indexOf(",", durStart);
            if (durEnd > durStart) {
                duration = data.substring(durStart, durEnd).toInt();
            }
        }

        if (duration <= 0) duration = 5;
        Queues::toState(makeAuthSuccessEvent(userName.c_str(), (uint16_t)duration));
    } else {
        Queues::toState(makeAuthFailedEvent());
    }
}

void MQTTClient::handleCommand(const char* payload, size_t len) {
    String data(payload);
    int cmdPos = data.indexOf("\"command\":");
    if (cmdPos < 0) return;

    int start = data.indexOf("\"", cmdPos + 10) + 1;
    int end = data.indexOf("\"", start);
    if (start <= 0 || end <= start) return;

    String cmd = data.substring(start, end);

    int param = 0;
    int paramPos = data.indexOf("\"param\":");
    if (paramPos >= 0) {
        int pStart = paramPos + 8;
        int pEnd = data.indexOf("}", pStart);
        if (pEnd < 0) pEnd = data.indexOf(",", pStart);
        if (pEnd > pStart) param = data.substring(pStart, pEnd).toInt();
    }

    Queues::toState(makeCommandEvent(cmd.c_str(), (int16_t)param));
}

void MQTTClient::publishStatus(LockState lockState) {
    if (!mqtt.connected()) return;

    String topic = baseTopic + "/status";
    char buffer[256];
    snprintf(buffer, sizeof(buffer),
        "{\"timestamp\":%lu,\"connected\":true,\"lock_state\":\"%s\",\"ip\":\"%s\"}",
        millis(),
        lockState == LockState::LOCKED ? "closed" : "opened",
        networkManager.getIP().c_str());

    mqtt.publish(topic.c_str(), buffer, true);
    lastStatusTime = millis();
}

void MQTTClient::publishEvent(const char* eventType, const char* data) {
    if (!mqtt.connected()) return;

    String topic = baseTopic + "/event";
    char buffer[256];
    snprintf(buffer, sizeof(buffer),
        "{\"type\":\"%s\",\"data\":\"%s\",\"timestamp\":%lu}",
        eventType, data, millis());

    mqtt.publish(topic.c_str(), buffer, false);
}

void MQTTClient::publishAuthRequest(const char* qrCode) {
    if (!mqtt.connected()) return;

    String topic = baseTopic + "/auth/request";
    char buffer[256];
    snprintf(buffer, sizeof(buffer),
        "{\"action\":\"auth_request\",\"qr_code\":\"%s\",\"timestamp\":%lu}",
        qrCode, millis());

    mqtt.publish(topic.c_str(), buffer);
}
