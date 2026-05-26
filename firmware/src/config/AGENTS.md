# src/config — Hardware Map & Persisted Settings

Two unrelated concerns colocated: pin assignments + sizing constants ([pins.h](/home/bitbyte08/Documents/Door.dot/src/config/pins.h)) and NVS-backed configuration ([ConfigManager](/home/bitbyte08/Documents/Door.dot/src/config/ConfigManager.h)).

## pins.h — Hardware Constraints

These are not arbitrary choices. The lolin_d32_pro (ESP32-WROVER) PSRAM and 8-bit parallel TFT pinout impose hard restrictions. Re-pinning requires re-reading the ESP32 datasheet.

| Pin | Use | Constraint |
|-----|-----|------------|
| **GPIO 16, 17** | reserved (PSRAM) | PSRAM uses these on WROVER. Never reassign. QR UART RX moved to GPIO 34 because of this. |
| **GPIO 34** | `QR_RX_PIN` | Input-only — fine for UART RX. `QR_TX_PIN = -1` (scanner doesn't need commands). |
| **GPIO 39** | `RESET_PIN` (disabled) | Input-only, **no internal pull-up**. The reset switch logic in [main.cpp `checkResetSwitch`](/home/bitbyte08/Documents/Door.dot/src/main.cpp) is commented out. To enable, add a 10 kΩ external pull-up and uncomment. |
| **GPIO 2** | `TFT_DC` | Also the onboard LED on most ESP32 dev boards. LED is disabled (`LED_PIN` commented out). Do not enable an LED on GPIO 2. |
| **GPIO 32** | `LOCK_PIN` | Relay control, `LOCK_ACTIVE_LOW = true`. HIGH = locked (relay off), LOW = unlocked. Inverting this without rewiring the relay will fail-open the door. |
| **GPIO 12–15, 21–22, 25–26** | `TFT_DB0..DB7` | NanoUI 8-bit parallel data bus. Do not reuse for anything else. |
| **GPIO 4, 27, 33, 2** | TFT control (WR, CS, RST, DC) | TFT_CS / TFT_DC are `#undef`'d before redefinition because the d32_pro variant pre-defines them. Preserve the `#ifdef ... #undef` block at the top of `pins.h`. |
| **GPIO 5, 18, 19, 23** | XPT2046 touch (CS + SPI) | Touch shares the SPI bus initialized in `UIManager::begin`. |

Sizing constants (queue sizes, task stacks, render FPS, MQTT cadence) also live here as `#define`s. NanoUI compile-time limits (`MAX_COMPONENTS_PER_SCREEN`, `MAX_SCREENS`, ...) live in [platformio.ini](/home/bitbyte08/Documents/Door.dot/platformio.ini) `build_flags`, not here.

## ConfigManager — NVS Wrapper

Singleton over Arduino `Preferences` (NVS namespace `"door"`). Holds a single `DoorConfig` POD: room code, WiFi creds, MQTT server/port, registered flag. `load()` runs in `begin()`; `save()` writes back fields that are non-empty (empty strings are skipped so partial saves don't blank existing values).

`isRegistered` is derived: set true on `load()` when `room_code` is non-empty, set true on `setRoomCode(non-empty)`. There is no explicit "register" call — writing the room code is the register operation.

## Anti-Patterns

- Do not call `prefs.begin("door", false)` from two tasks concurrently. NVS is not thread-safe; serialize writes via `StateManagerTask` or take `Mutexes::configMutex` (currently unused — see [core/AGENTS.md](/home/bitbyte08/Documents/Door.dot/src/core/AGENTS.md)).
- Do not save credentials without `setWiFi(ssid, pass)` first — `save()` skips empty strings to preserve prior values, so a half-populated `DoorConfig` will leave stale data on flash.
- Do not introduce new pins without checking ESP32 strapping pins (0, 2, 5, 12, 15) — wrong levels at boot will brick the device or force download mode.
- Do not change `MQTT_STATUS_INTERVAL_MS` below ~5 s without verifying broker QoS; the LWT relies on keepalive (60 s in [MQTTClient.cpp](/home/bitbyte08/Documents/Door.dot/src/network/MQTTClient.cpp)).
