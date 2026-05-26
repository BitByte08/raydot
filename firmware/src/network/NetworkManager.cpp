#include "NetworkManager.h"
#include "core/Queues.h"

NetworkManager& NetworkManager::getInstance() {
    static NetworkManager instance;
    return instance;
}

NetworkManager& networkManager = NetworkManager::getInstance();

void NetworkManager::begin() {
    const DoorConfig& cfg = configManager.getConfig();
    
    // WiFi credentials가 없으면 AP 모드로 시작
    if (strlen(cfg.wifiSSID) == 0) {
        Serial.println("[NET] No WiFi config, starting AP mode");
        startAPMode();
        return;
    }
    
    initWiFi();
}

void NetworkManager::startAPMode() {
    apMode = true;
    
    // AP 이름: DoorDot-XXXX (마지막 4자리 MAC)
    uint8_t mac[6];
    WiFi.macAddress(mac);
    snprintf(apName, sizeof(apName), "DoorDot-%02X%02X", mac[4], mac[5]);
    
    WiFi.mode(WIFI_AP);
    WiFi.softAP(apName, "door1234");  // 기본 비번: door1234
    
    Serial.printf("[NET] AP started: %s, IP: %s\n", 
                  apName, WiFi.softAPIP().toString().c_str());
    
    setupWebServer();
}

void NetworkManager::stopAPMode() {
    if (server) {
        server->stop();
        delete server;
        server = nullptr;
    }
    WiFi.softAPdisconnect(true);
    apMode = false;
}

void NetworkManager::setupWebServer() {
    server = new WebServer(80);
    
    server->on("/", [this]() { handleRoot(); });
    server->on("/save", [this]() { handleSave(); });
    
    server->begin();
    Serial.println("[NET] Web server started on port 80");
}

void NetworkManager::handleRoot() {
    const char* html = R"(
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DoorDot Setup</title>
    <style>
        body { font-family: Arial; margin: 20px; background: #1a1a1a; color: #fff; }
        input { width: 100%; padding: 10px; margin: 5px 0; box-sizing: border-box; }
        button { width: 100%; padding: 12px; background: #00b4d8; color: #fff; border: none; font-size: 16px; cursor: pointer; }
        button:hover { background: #0096c7; }
        .container { max-width: 400px; margin: 0 auto; }
        h1 { text-align: center; }
    </style>
</head>
<body>
    <div class="container">
        <h1>DoorDot Setup</h1>
        <form action="/save" method="post">
            <label>WiFi SSID:</label>
            <input type="text" name="ssid" required>
            <label>WiFi Password:</label>
            <input type="password" name="wifipass">
            <label>MQTT Server:</label>
            <input type="text" name="mqttserver" value="192.168.1.100">
            <label>MQTT Port:</label>
            <input type="number" name="mqttport" value="1883">
            <br><br>
            <button type="submit">Save & Reboot</button>
        </form>
    </div>
</body>
</html>
)";
    server->send(200, "text/html", html);
}

void NetworkManager::handleSave() {
    String ssid = server->arg("ssid");
    String wifipass = server->arg("wifipass");
    String mqttserver = server->arg("mqttserver");
    int mqttport = server->arg("mqttport").toInt();
    
    if (ssid.length() > 0) {
        configManager.setWiFi(ssid.c_str(), wifipass.c_str());
        configManager.setMQTT(mqttserver.c_str(), mqttport);
        configManager.save();
        
        server->send(200, "text/html", "<h1>Saved! Rebooting...</h1><p>Connect to your WiFi and the device will restart.</p>");
        
        delay(2000);
        ESP.restart();
    } else {
        server->send(400, "text/html", "<h1>Error: SSID required</h1><a href='/'>Back</a>");
    }
}

void NetworkManager::initWiFi() {
    const DoorConfig& cfg = configManager.getConfig();
    if (strlen(cfg.wifiSSID) == 0) {
        Serial.println("[NET] No WiFi credentials");
        return;
    }

    Serial.printf("[NET] Connecting to %s", cfg.wifiSSID);
    WiFi.mode(WIFI_STA);
    WiFi.setSleep(false);
    WiFi.begin(cfg.wifiSSID, cfg.wifiPass);

    int attempts = 0;
    while (WiFi.status() != WL_CONNECTED && attempts < 30) {
        delay(500);
        Serial.print(".");
        attempts++;
        
        // 상태 이벤트 발행
        if (attempts % 4 == 0) {
            Queues::toRender(makeNetworkEvent(false));
        }
    }

    if (WiFi.status() == WL_CONNECTED) {
        wifiConnected = true;
        currentType = NetworkType::WIFI;
        Serial.printf("\n[NET] WiFi IP: %s\n", WiFi.localIP().toString().c_str());
        Queues::toRender(makeNetworkEvent(true));
    } else {
        Serial.println("\n[NET] WiFi failed, starting AP mode");
        Queues::toRender(makeNetworkEvent(false));
        startAPMode();
    }
}

void NetworkManager::checkConnection() {
    if (apMode) return;
    
    if (WiFi.status() != WL_CONNECTED) {
        if (wifiConnected) {
            wifiConnected = false;
            currentType = NetworkType::NONE;
            Queues::toRender(makeNetworkEvent(false));
        }
        WiFi.reconnect();
    } else if (!wifiConnected) {
        wifiConnected = true;
        currentType = NetworkType::WIFI;
        Queues::toRender(makeNetworkEvent(true));
    }
}

void NetworkManager::update() {
    if (apMode && server) {
        server->handleClient();
        return;
    }
    
    if (millis() - lastCheck > 5000) {
        checkConnection();
        lastCheck = millis();
    }
}

bool NetworkManager::isConnected() const {
    if (apMode) return false;
    return wifiConnected && currentType == NetworkType::WIFI;
}

NetworkType NetworkManager::getType() const {
    return currentType;
}

String NetworkManager::getIP() const {
    if (apMode) return WiFi.softAPIP().toString();
    if (currentType == NetworkType::WIFI) return WiFi.localIP().toString();
    return "0.0.0.0";
}

bool NetworkManager::setWiFiCredentials(const char* ssid, const char* pass) {
    configManager.setWiFi(ssid, pass);
    configManager.save();
    return true;
}
