#include "ConfigManager.h"

ConfigManager& ConfigManager::getInstance() {
    static ConfigManager instance;
    return instance;
}

ConfigManager& configManager = ConfigManager::getInstance();

void ConfigManager::begin() {
    load();
}

bool ConfigManager::load() {
    prefs.begin("door", true);

    String rc = prefs.getString("room_code", "");
    if (rc.length() > 0) {
        strncpy(config.roomCode, rc.c_str(), sizeof(config.roomCode) - 1);
        config.isRegistered = true;
    }

    String ssid = prefs.getString("wifi_ssid", "");
    strncpy(config.wifiSSID, ssid.c_str(), sizeof(config.wifiSSID) - 1);

    String pass = prefs.getString("wifi_pass", "");
    strncpy(config.wifiPass, pass.c_str(), sizeof(config.wifiPass) - 1);

    String server = prefs.getString("mqtt_server", "");
    strncpy(config.mqttServer, server.c_str(), sizeof(config.mqttServer) - 1);

    config.mqttPort = prefs.getInt("mqtt_port", 1883);

    prefs.end();

    return config.isRegistered;
}

bool ConfigManager::save() {
    prefs.begin("door", false);

    if (strlen(config.roomCode) > 0) {
        prefs.putString("room_code", config.roomCode);
    }
    if (strlen(config.wifiSSID) > 0) {
        prefs.putString("wifi_ssid", config.wifiSSID);
    }
    if (strlen(config.wifiPass) > 0) {
        prefs.putString("wifi_pass", config.wifiPass);
    }
    if (strlen(config.mqttServer) > 0) {
        prefs.putString("mqtt_server", config.mqttServer);
    }
    prefs.putInt("mqtt_port", config.mqttPort);

    prefs.end();
    return true;
}

void ConfigManager::clear() {
    prefs.begin("door", false);
    prefs.clear();
    prefs.end();
    config = DoorConfig();
}

void ConfigManager::setRoomCode(const char* code) {
    strncpy(config.roomCode, code, sizeof(config.roomCode) - 1);
    config.roomCode[sizeof(config.roomCode) - 1] = '\0';
    config.isRegistered = (strlen(code) > 0);
}

void ConfigManager::setWiFi(const char* ssid, const char* pass) {
    strncpy(config.wifiSSID, ssid, sizeof(config.wifiSSID) - 1);
    config.wifiSSID[sizeof(config.wifiSSID) - 1] = '\0';
    strncpy(config.wifiPass, pass, sizeof(config.wifiPass) - 1);
    config.wifiPass[sizeof(config.wifiPass) - 1] = '\0';
}

void ConfigManager::setMQTT(const char* server, int port) {
    strncpy(config.mqttServer, server, sizeof(config.mqttServer) - 1);
    config.mqttServer[sizeof(config.mqttServer) - 1] = '\0';
    config.mqttPort = port;
}
