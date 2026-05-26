# Network 연결 구현

## 요구사항

- 제안 1: BLE → WiFi 정보 전송 (Reset Switch 배치 필요)
- 제안 2: ETH (LAN선) - **채택**

## 구현 방안

### 채택: Ethernet (ETH) + WiFi 백업

ETH를 기본으로 사용하되, WiFi도 지원하여 유연성 확보.

```cpp
enum class NetworkType {
    ETHERNET,
    WIFI,
    NONE
};

class NetworkManager {
public:
    void begin();
    void update();
    bool isConnected();
    NetworkType getType();
    String getIP();
    
    // WiFi 설정 (BLE를 통해 수신)
    bool setWiFiCredentials(const String& ssid, const String& password);
    
private:
    NetworkType currentType;
    bool ethConnected;
    bool wifiConnected;
    
    void initEthernet();
    void initWiFi();
    void checkConnection();
};

extern NetworkManager networkManager;
```

## Ethernet 초기화 (W5500)

### 핀 설정

| 핀 | 용도 | ESP32 핀 |
|---|------|----------|
| CS | 칩 선택 | 5 |
| SCK | 클럭 | 18 |
| MISO | 데이터 입력 | 19 |
| MOSI | 데이터 출력 | 23 |
| INT | 인터럽트 | 4 (선택) |

```cpp
#include <Ethernet.h>
#include <SPI.h>

#define ETH_CS 5
#define ETH_SCK 18
#define ETH_MISO 19
#define ETH_MOSI 23

byte mac[] = { 0xDE, 0xAD, 0xBE, 0xEF, 0xFE, 0xED };

void NetworkManager::initEthernet() {
    SPI.begin(ETH_SCK, ETH_MISO, ETH_MOSI);
    Ethernet.init(ETH_CS);
    
    // DHCP로 IP 할당
    if (Ethernet.begin(mac) == 0) {
        Serial.println("DHCP failed, using static IP");
        Ethernet.begin(mac, IPAddress(192, 168, 1, 100));
    }
    
    delay(1000);
    
    if (Ethernet.linkStatus() == LinkON) {
        ethConnected = true;
        currentType = NetworkType::ETHERNET;
        Serial.print("Ethernet IP: ");
        Serial.println(Ethernet.localIP());
    }
}
```

### 연결 상태 확인

```cpp
void NetworkManager::checkConnection() {
    if (currentType == NetworkType::ETHERNET) {
        // W5500은 링크 상태 확인
        if (Ethernet.linkStatus() == LinkOFF) {
            ethConnected = false;
            // WiFi로 폴백
            initWiFi();
        }
    }
}

void NetworkManager::update() {
    // 주기적으로 연결 상태 확인 (loop에서 호출)
    static unsigned long lastCheck = 0;
    if (millis() - lastCheck > 5000) {
        checkConnection();
        lastCheck = millis();
    }
}
```

## WiFi 초기화

```cpp
#include <WiFi.h>

void NetworkManager::initWiFi() {
    if (configManager.getConfig().wifiSSID.isEmpty()) {
        Serial.println("No WiFi credentials");
        return;
    }
    
    WiFi.mode(WIFI_STA);
    WiFi.begin(
        configManager.getConfig().wifiSSID.c_str(),
        configManager.getConfig().wifiPass.c_str()
    );
    
    int attempts = 0;
    while (WiFi.status() != WL_CONNECTED && attempts < 20) {
        delay(500);
        Serial.print(".");
        attempts++;
    }
    
    if (WiFi.status() == WL_CONNECTED) {
        wifiConnected = true;
        currentType = NetworkType::WIFI;
        Serial.print("WiFi IP: ");
        Serial.println(WiFi.localIP());
    }
}
```

## BLE 설정 모드 (선택적)

Reset Switch 짧게 누름 시 BLE 모드 진입:

```cpp
#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>
#include <BLE2902.h>

#define BLE_SERVICE_UUID        "4fafc201-1fb5-459e-8fcc-c5c9c331914b"
#define BLE_CHARACTERISTIC_UUID "beb5483e-36e1-4688-b7f5-ea07361b26a8"

class BLEConfigManager {
public:
    void begin();
    void startAdvertising();
    bool hasNewConfig();
    WiFiConfig getWiFiConfig();
    
private:
    BLEServer* pServer;
    BLECharacteristic* pCharacteristic;
    String receivedData;
    bool newData;
};

void BLEConfigManager::begin() {
    BLEDevice::init("DoorDot-Setup");
    pServer = BLEDevice::createServer();
    BLEService* pService = pServer->createService(BLE_SERVICE_UUID);
    
    pCharacteristic = pService->createCharacteristic(
        BLE_CHARACTERISTIC_UUID,
        BLECharacteristic::PROPERTY_WRITE
    );
    
    pService->start();
}

void BLEConfigManager::startAdvertising() {
    BLEAdvertising* pAdvertising = BLEDevice::createAdvertising();
    pAdvertising->addServiceUUID(BLE_SERVICE_UUID);
    pAdvertising->setScanResponse(false);
    pAdvertising->setMinPreferred(0x0);
    BLEDevice::startAdvertising();
}
```

### WiFi 설정 JSON 형식

```json
{
  "ssid": "WiFi이름",
  "password": "비밀번호"
}
```

## 연결 상태 발행

NetworkManager는 MQTT Manager에게 연결 상태 전달:

```cpp
bool NetworkManager::isConnected() {
    switch (currentType) {
        case NetworkType::ETHERNET:
            return ethConnected;
        case NetworkType::WIFI:
            return wifiConnected;
        default:
            return false;
    }
}

String NetworkManager::getIP() {
    switch (currentType) {
        case NetworkType::ETHERNET:
            return Ethernet.localIP().toString();
        case NetworkType::WIFI:
            return WiFi.localIP().toString();
        default:
            return "0.0.0.0";
    }
}
```

## main.cpp 통합

```cpp
void setup() {
    Serial.begin(115200);
    configManager.begin();
    uiManager.begin();
    networkManager.begin();
    
    if (!configManager.isRegistered()) {
        uiManager.showScreen(Screen::REGISTRATION);
    }
}

void loop() {
    uiManager.update();
    networkManager.update();
    
    // 연결 상태 UI 업데이트
    uiManager.setWiFiStatus(networkManager.isConnected());
    
    // MQTT 업데이트
    mqttManager.update();
}
```

## platformio.ini 라이브러리 추가

```ini
lib_deps =
    https://github.com/bssm-oss/NanoUI.git
    Ethernet
```

## 파일 구조

```
src/
├── network/
│   ├── NetworkManager.h
│   ├── NetworkManager.cpp
│   ├── BLEConfig.h        (선택적)
│   └── BLEConfig.cpp      (선택적)
└── main.cpp
```

## 하드웨어 연결도

```
ESP32 (LOLIN D32 Pro)
       │
       ├── W5500 Ethernet Module
       │      CS  → GPIO 5
       │      SCK → GPIO 18
       │      MISO → GPIO 19
       │      MOSI → GPIO 23
       │      VCC → 3.3V
       │      GND → GND
       │
       └── Antenna (내장 WiFi)
```