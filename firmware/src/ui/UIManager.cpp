#include "UIManager.h"
#include "ui/screens.h"
#include "config/pins.h"
#include <SPI.h>

UIManager& UIManager::getInstance() {
    static UIManager instance;
    return instance;
}

UIManager& uiManager = UIManager::getInstance();

const char* UIManager::screenId(Screen s) {
    switch (s) {
        case Screen::WIFI_SETUP:    return "wifi_setup";
        case Screen::REGISTRATION:  return "registration";
        case Screen::REGISTERED:    return "registered";
        case Screen::CLOSED:        return "closed";
        case Screen::OPENED:        return "opened";
        case Screen::ERROR:         return "error";
        default:                    return "registration";
    }
}

void UIManager::begin() {
    SPI.begin(TOUCH_SCK, TOUCH_MISO, TOUCH_MOSI);
    ui.beginParallel(TFT_CS, TFT_DC, TFT_WR, TFT_RST,
                      TFT_DB0, TFT_DB1, TFT_DB2, TFT_DB3,
                      TFT_DB4, TFT_DB5, TFT_DB6, TFT_DB7,
                      TOUCH_CS);
    ui.loadFromFlash(UI_JSON);
    initialized = true;
    Serial.println("[UI] Initialized (Parallel)");
}

void UIManager::update() {
    if (!initialized) return;
    ui.update();
}

void UIManager::showScreen(Screen screen) {
    if (!initialized) return;
    if (currentScreen == screen) return;

    currentScreen = screen;
    ui.show(screenId(screen));

    // 화면 전환 시 상태 추적 초기화
    lastTimerValue = -1;
    Serial.printf("[UI] Screen: %s\n", screenId(screen));
}

void UIManager::setAPName(const char* name) {
    if (!initialized) return;
    char buf[32];
    snprintf(buf, sizeof(buf), "AP: %s", name);
    ui.setText("lbl_ap", buf);
}

void UIManager::setRoomCode(const char* code) {
    if (!initialized) return;
    char buf[48];
    snprintf(buf, sizeof(buf), "Room: %s", code);
    ui.setText("lbl_room", buf);
}

void UIManager::setMQTTStatus(bool connected) {
    if (!initialized) return;
    if (lastMQTTConnected == connected) return;
    lastMQTTConnected = connected;
    ui.setText("lbl_mqtt", connected ? "MQTT: ON" : "MQTT: OFF");
}

void UIManager::setNetworkStatus(bool connected) {
    if (!initialized) return;
    if (lastNetworkConnected == connected) return;
    lastNetworkConnected = connected;
    ui.setText("lbl_wifi", connected ? "NET: ON" : "NET: OFF");
}

void UIManager::setOpenTimer(int remaining, int total) {
    if (!initialized) return;
    if (lastTimerValue == remaining) return;
    lastTimerValue = remaining;

    char buf[8];
    snprintf(buf, sizeof(buf), "%d", remaining);
    ui.setText("lbl_timer", buf);
}

void UIManager::setUserName(const char* name) {
    if (!initialized) return;
    char buf[48];
    snprintf(buf, sizeof(buf), "User: %s", name);
    ui.setText("lbl_user", buf);
}

void UIManager::setErrorMsg(const char* msg) {
    if (!initialized) return;
    ui.setText("lbl_error", msg);
}
