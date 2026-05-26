#pragma once

#include <Arduino.h>
#include <PubSubClient.h>
#include <WiFi.h>
#include "config/ConfigManager.h"
#include "config/pins.h"
#include "core/Events.h"

class MQTTClient {
public:
    static MQTTClient& getInstance();

    void begin();
    void update();
    bool isConnected();

    void publishStatus(LockState lockState);
    void publishEvent(const char* eventType, const char* data);
    void publishAuthRequest(const char* qrCode);

private:
    MQTTClient() = default;

    WiFiClient wifiClient;
    PubSubClient mqtt;
    String baseTopic;
    unsigned long lastStatusTime = 0;

    void connect();
    void subscribe();
    static void staticCallback(char* topic, byte* payload, unsigned int length);
    void handleCallback(char* topic, byte* payload, unsigned int length);
    void handleAuthResponse(const char* payload, size_t len);
    void handleCommand(const char* payload, size_t len);
};

extern MQTTClient& mqttClient;
