#include "MQTTClient.h"
#include "network/NetworkManager.h"
#include "core/Queues.h"
#include <ArduinoJson.h>

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
    JsonDocument doc;
    DeserializationError err = deserializeJson(doc, payload, len);
    if (err) {
        Serial.printf("[MQTT] JSON parse error: %s\n", err.c_str());
        return;
    }

    bool success = doc["success"] | false;
    if (!success) {
        Queues::toState(makeAuthFailedEvent());
        return;
    }

    const char* name = doc["user_name"] | "Unknown";
    int duration = doc["duration"] | 5;
    if (duration <= 0) duration = 5;

    Queues::toState(makeAuthSuccessEvent(name, (uint16_t)duration));
}

void MQTTClient::handleCommand(const char* payload, size_t len) {
    JsonDocument doc;
    DeserializationError err = deserializeJson(doc, payload, len);
    if (err) return;

    const char* cmd = doc["command"] | "";
    if (cmd[0] == '\0') return;

    int param = doc["param"] | 0;
    Event e = makeCommandEvent(cmd, param);
    Queues::toState(e);
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
