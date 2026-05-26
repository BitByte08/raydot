#pragma once

#include <Arduino.h>
#include <NanoUI.h>
#include "core/Events.h"

enum class Screen : uint8_t {
    WIFI_SETUP,
    REGISTRATION,
    REGISTERED,
    CLOSED,
    OPENED,
    ERROR
};

class UIManager {
public:
    static UIManager& getInstance();

    void begin();
    void update();  // ui.update() 호출

    // 화면 전환
    void showScreen(Screen screen);
    Screen getCurrentScreen() const { return currentScreen; }

    // 개별 업데이트
    void setAPName(const char* name);
    void setRoomCode(const char* code);
    void setMQTTStatus(bool connected);
    void setNetworkStatus(bool connected);
    void setOpenTimer(int remaining, int total);
    void setUserName(const char* name);
    void setErrorMsg(const char* msg);

private:
    UIManager() = default;

    NanoUI::NanoUI ui;
    Screen currentScreen = static_cast<Screen>(0xFF);
    bool initialized = false;

    // 상태 추적 (불필요한 업데이트 방지)
    bool lastMQTTConnected = false;
    bool lastNetworkConnected = false;
    int lastTimerValue = -1;

    const char* screenId(Screen s);
};

extern UIManager& uiManager;
