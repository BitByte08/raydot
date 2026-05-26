#pragma once

#include <Arduino.h>
#include "config/pins.h"
#include "core/Events.h"

class QRScanner {
public:
    static QRScanner& getInstance();

    void begin();
    bool scan();  // true if new code available

    QRType getType()   const { return lastType; }
    const char* getCode() const { return lastCode; }

    void setMinInterval(unsigned long ms);
    void clear();

private:
    QRScanner() = default;

    char lastCode[64] = "";
    QRType lastType = QRType::UNKNOWN;
    unsigned long lastReadTime = 0;
    unsigned long minInterval = QR_MIN_INTERVAL_MS;
    String buffer;
    bool initialized = false;

    QRType parseType(const char* data);
};

extern QRScanner& qrScanner;
