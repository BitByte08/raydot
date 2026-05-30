#include "QRScanner.h"
#include "config/pins.h"

QRScanner& QRScanner::getInstance() {
    static QRScanner instance;
    return instance;
}

QRScanner& qrScanner = QRScanner::getInstance();

void QRScanner::begin() {
    Serial2.begin(115200, SERIAL_8N1, QR_RX_PIN, QR_TX_PIN);
    buffer.reserve(128);
    initialized = true;
    Serial.println("[QR] Scanner initialized (115200)");
}

bool QRScanner::scan() {
    if (!initialized) return false;

    while (Serial2.available()) {
        char c = Serial2.read();

        if (c == '\n' || c == '\r') {
            if (buffer.length() > 0) {
                if (millis() - lastReadTime < minInterval) {
                    buffer = "";
                    continue;
                }

                if (buffer == lastCode && millis() - lastReadTime < 500) {
                    buffer = "";
                    continue;
                }

                buffer.trim();
                strncpy(lastCode, buffer.c_str(), sizeof(lastCode) - 1);
                lastCode[sizeof(lastCode) - 1] = '\0';
                lastType = parseType(lastCode);
                lastReadTime = millis();
                buffer = "";

                Serial.printf("[QR] Scanned: %s (type=%d)\n", lastCode, (int)lastType);
                return true;
            }
        } else if (isPrintable(c)) {
            buffer += c;
            if (buffer.length() >= 127) {
                buffer = "";
            }
        }
    }

    return false;
}

QRType QRScanner::parseType(const char* data) {
    if (strncmp(data, "ROOM:", 5) == 0) return QRType::ROOM_CODE;
    if (strncmp(data, "USER:", 5) == 0) return QRType::USER_CODE;
    return QRType::UNKNOWN;
}

void QRScanner::setMinInterval(unsigned long ms) {
    minInterval = ms;
}

void QRScanner::tryBaud(unsigned long baud) {
    Serial2.begin(baud, SERIAL_8N1, QR_RX_PIN, QR_TX_PIN);
}

void QRScanner::clear() {
    lastCode[0] = '\0';
    lastType = QRType::UNKNOWN;
    buffer = "";
}
