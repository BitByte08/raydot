#pragma once

#include <Arduino.h>
#include <WiFi.h>
#include <WebServer.h>
#include "config/ConfigManager.h"
#include "config/pins.h"
#include "core/Events.h"

class NetworkManager {
public:
    static NetworkManager& getInstance();

    void begin();
    void update();

    bool isConnected() const;
    NetworkType getType() const;
    String getIP() const;

    bool setWiFiCredentials(const char* ssid, const char* pass);
    
    // AP Mode
    bool isInAPMode() const { return apMode; }
    void startAPMode();
    void stopAPMode();
    const char* getAPName() const { return apName; }

private:
    NetworkManager() = default;

    NetworkType currentType = NetworkType::NONE;
    bool wifiConnected = false;
    bool apMode = false;
    char apName[20] = {};
    unsigned long lastCheck = 0;
    WebServer* server = nullptr;

    void initWiFi();
    void checkConnection();
    void setupWebServer();
    void handleRoot();
    void handleSave();
};

extern NetworkManager& networkManager;
