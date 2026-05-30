#include "QRScanner.h"
#include "config/pins.h"

QRScanner& QRScanner::getInstance() {
    static QRScanner instance;
    return instance;
}

QRScanner& qrScanner = QRScanner::getInstance();

void QRScanner::begin() {
    Serial2.begin(9600, SERIAL_8N1, QR_RX_PIN, QR_TX_PIN);
    buffer.reserve(128);
    initialized = true;
    Serial.println("[QR] Scanner initialized");
}

bool QRScanner::scan() {
    if (!initialized) return false;

    // 시리얼 버퍼 읽기
    int available = Serial2.available();
    if (available > 0) {
        Serial.printf("[QR] DEBUG: %d bytes waiting\n", available);
    }

    while (Serial2.available()) {
        char c = Serial2.read();
        Serial.printf("[QR] RAW byte: 0x%02X '%c'\n", (unsigned char)c, isPrintable(c) ? c : '.');

        if (c == '\n' || c == '\r') {
            if (buffer.length() > 0) {
                // 속도 제한 체크
                if (millis() - lastReadTime < minInterval) {
                    buffer = "";
                    continue;
                }

                // 디바운싱: 같은 코드 반복 무시
                if (buffer == lastCode && millis() - lastReadTime < 500) {
                    buffer = "";
                    continue;
                }

                // 코드 파싱
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
            // 버퍼 오버플로우 방지
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

void QRScanner::clear() {
    lastCode[0] = '\0';
    lastType = QRType::UNKNOWN;
    buffer = "";
}
