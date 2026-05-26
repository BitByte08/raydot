# Door.dot — Project Knowledge Base

**Generated:** 2026-05-26 (Asia/Seoul) | **Commit:** 0571557 | **Branch:** master

## Overview

ESP32 firmware for a study-room (정독실) electromagnetic door lock. QR scan → MQTT auth → relay open. Built on PlatformIO + Arduino framework, organized as 5 FreeRTOS tasks communicating via 3 queues. Target board: `lolin_d32_pro` (ESP32-WROVER, 4MB PSRAM).

## Structure

```
.
├── platformio.ini    # ONLY build config — VSCode c_cpp_properties.json is auto-generated, do not edit
├── src/
│   ├── main.cpp      # setup() wires modules + starts tasks; loop() is empty
│   ├── config/       # ConfigManager (NVS) + pins.h (hardware map, critical gotchas)
│   ├── core/         # Events.h + Queues + Mutexes — shared comms primitives
│   ├── tasks/        # FreeRTOS task subclasses (one .h-only file per task)
│   ├── ui/           # NanoUI wrapper + JSON screen defs (PROGMEM)
│   ├── network/      # WiFi STA + AP-mode captive setup + MQTT
│   ├── scanner/      # UART QR reader (Serial2)
│   └── lock/         # GPIO relay driver with software timer
├── docs/             # Aspirational design docs — STALE, see warning below
├── include/, lib/, test/   # PlatformIO scaffolding, unused
└── .pio/, .venv/     # Build + Python tool caches, gitignored
```

## Where to Look

| Task | Location |
|------|----------|
| Add a new event type | [src/core/Events.h](/home/bitbyte08/Documents/Door.dot/src/core/Events.h) (enum + builder + union member) |
| Wire a new module into the state machine | [src/tasks/StateManagerTask.h](/home/bitbyte08/Documents/Door.dot/src/tasks/StateManagerTask.h) `handleEvent()` |
| Change pin assignment | [src/config/pins.h](/home/bitbyte08/Documents/Door.dot/src/config/pins.h) — read hardware gotchas first |
| Change MQTT topic / payload | [src/network/MQTTClient.cpp](/home/bitbyte08/Documents/Door.dot/src/network/MQTTClient.cpp) |
| Add a screen | [src/ui/screens.h](/home/bitbyte08/Documents/Door.dot/src/ui/screens.h) (JSON in `PROGMEM`) + `Screen` enum + `screenId()` map in [UIManager.cpp](/home/bitbyte08/Documents/Door.dot/src/ui/UIManager.cpp) |
| Tune task stack / priority / core | [src/config/pins.h](/home/bitbyte08/Documents/Door.dot/src/config/pins.h) `*_TASK_STACK` + constructor in each `tasks/*Task.h` |
| Add a build flag | [platformio.ini](/home/bitbyte08/Documents/Door.dot/platformio.ini) `build_flags` |

## Architecture

Event-driven, single producer-per-queue. Three queues with directional flow:

```
QRScannerTask ─┐
NetworkTask ───┼─→ eventQueue ──→ StateManagerTask ──┐
LockTask*      │                                      ├─→ renderQueue ──→ RenderTask
               │                                      │
StateManager ──┴─→ networkQueue ──→ (reserved)        ├─→ MQTT publish (direct, not queued)
                                                      └─→ EMLockManager (direct call)

* LockTask polls EMLockManager + emits LOCK_TIMER_UPDATE to renderQueue
```

`StateManagerTask` is the single consumer of `eventQueue` and the only state mutator. All cross-module mutation flows through it. `RenderTask` is the only consumer of `renderQueue`. Modules talk to MQTT and the relay via direct method calls on the singletons — these are safe because each is called from exactly one task.

## Conventions

- **Singletons**: every module exposes `static Foo& getInstance()` + a free `extern Foo& fooManager` reference. Define the reference in the `.cpp` immediately after `getInstance()`. Never construct instances elsewhere.
- **Headers**: `#pragma once` (not include guards). Header-only is fine for tasks (see `src/tasks/`).
- **Tasks**: subclass `TaskBase`, implement `void run() override` with a `while (running)` loop. Constructor passes name/stack/priority/core to base. See [src/tasks/AGENTS.md](/home/bitbyte08/Documents/Door.dot/src/tasks/AGENTS.md).
- **Events**: build with `makeXxxEvent(...)` helpers, never construct `Event` literals. Send via `Queues::toState() / toRender() / toNetwork()`. See [src/core/AGENTS.md](/home/bitbyte08/Documents/Door.dot/src/core/AGENTS.md).
- **Strings**: fixed-size `char[N]` in event union, copied with `strncpy(dst, src, sizeof(dst) - 1)`. No `std::string`. `Arduino String` only inside `*.cpp` (parsing/formatting), never across task boundaries.
- **JSON**: ArduinoJson is in `lib_ldf_mode = deep+` discovery but unused. MQTT payload parsing is hand-rolled `indexOf` in [MQTTClient.cpp](/home/bitbyte08/Documents/Door.dot/src/network/MQTTClient.cpp). Match this style for incoming payloads.
- **Constants**: `#define` for hardware + sizing constants in `pins.h`; `constexpr` not used. Compile-time NanoUI sizing goes in `platformio.ini` `build_flags`, not headers.
- **Comments**: Korean is fine and used throughout. Pin gotcha comments are required (see `pins.h`).
- **Logging**: `Serial.printf("[TAG] ...", ...)` with bracketed tag matching the module (`[QR]`, `[MQTT]`, `[STATE]`, `[NET]`, `[LOCK]`, `[UI]`, `[CONFIG]`, `[RTOS]`, `[RESET]`).

## Anti-Patterns (this project)

- Do not call `xQueueSend` directly — go through `Queues::toState/toRender/toNetwork`.
- Do not call `digitalWrite(LOCK_PIN, ...)` from anywhere except `EMLockManager::setHardware()`; lock state must stay consistent with `LockState`.
- Do not edit `.vscode/c_cpp_properties.json` — auto-generated by `pio init`.
- Do not add `GPIO 16/17` for any new peripheral (PSRAM-conflicted). Do not use `GPIO 2` for an LED (collides with `TFT_DC`). Do not arm the GPIO 39 reset switch without external pull-up — see [main.cpp `checkResetSwitch`](/home/bitbyte08/Documents/Door.dot/src/main.cpp:35).
- Do not block inside `RenderTask` — keep handlers short. SPI bus is shared (Touch + TFT_CS); the UI mutex exists but is currently unused because Render is the sole UI consumer.
- Do not introduce `delay()` inside task loops — use `vTaskDelay()` / `vTaskDelayUntil()` (`delayMs()` helper on `TaskBase`).
- Do not parse MQTT payloads with ArduinoJson without first removing the existing hand-rolled parser and budgeting the heap cost.
- Do not amend events or remove enum cases — `StateManagerTask::handleEvent` has a default branch but `RenderTask` and `MQTTClient` do `indexOf` literals; renaming requires touching all three.

## Build & Run

```bash
# Use PlatformIO from the project .venv (auto-installed by `pio init`)
.venv/bin/pio run                          # compile
.venv/bin/pio run --target upload          # flash over USB
.venv/bin/pio device monitor               # 115200 baud, esp32_exception_decoder
.venv/bin/pio run --target clean
```

No host tests, no CI. `test/README` is the empty PlatformIO scaffold. Verification is on-device via Serial Monitor (decoder filter is enabled).

## Provisioning Flow

1. First boot, no `wifi_ssid` in NVS → `NetworkManager` enters `apMode`, opens AP `DoorDot-XXXX` (PW `door1234`), serves HTML form on `192.168.4.1`. UI shows `WIFI_SETUP` screen.
2. User POSTs SSID/pass/MQTT to `/save` → config written to NVS → `ESP.restart()`.
3. Post-reboot with WiFi but no `room_code` → UI shows `REGISTRATION`. Admin scans `ROOM:xxx` QR → `StateManagerTask::handleQR` stores it and restarts.
4. Post-reboot registered + WiFi up + MQTT connected → `READY`. Scan `USER:xxx` → publish to `door/{roomCode}/auth/request`. Server responds on `/auth/response` → open relay for `duration` seconds.

MQTT topic tree: `door/{roomCode}/{status,event,auth/request,auth/response,command}`. LWT publishes `{"connected":false}` to `/status`.

## Stale Docs Warning

`docs/*.md` are pre-implementation design notes. The implementation has diverged:

| Doc says | Code actually has |
|---|---|
| `LED_PIN = 2` | Disabled — conflicts with `TFT_DC` |
| Ethernet/W5500 pins, `NetworkType::ETHERNET` flow | WiFi-only; Ethernet enum exists but is never assigned |
| `MQTT_CONNECTED/DISCONNECTED` events | Renamed to `MQTT_LINKED/MQTT_LOST` |
| `REGISTRATION_COMPLETE` event | Split into `REGISTRATION_SUCCESS/FAILED` (neither emitted yet) |
| Separate `core/StateManager.{h,cpp}` | Logic lives in `tasks/StateManagerTask.h` |
| Separate `Mutexes.h/cpp` | Merged into `core/Queues.{h,cpp}` |
| `Ticker`, `serialMutex`, `UI_UPDATE` event | Not implemented |

When in doubt, code wins. Treat `docs/` as historical context, not specification.
