#pragma once

#include <Arduino.h>
#include <Preferences.h>

struct DoorConfig {
    char roomCode[32]     = "";
    char wifiSSID[64]     = "";
    char wifiPass[64]     = "";
    char mqttServer[64]   = "";
    int  mqttPort         = 1883;
    bool isRegistered     = false;
};

class ConfigManager {
public:
    static ConfigManager& getInstance();

    void begin();
    bool load();
    bool save();
    void clear();

    const DoorConfig& getConfig() const { return config; }

    void setRoomCode(const char* code);
    void setWiFi(const char* ssid, const char* pass);
    void setMQTT(const char* server, int port);

    bool isRegistered() const { return config.isRegistered; }

private:
    ConfigManager() = default;
    DoorConfig config;
    Preferences prefs;
};

extern ConfigManager& configManager;
