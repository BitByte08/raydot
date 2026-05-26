# src/core — Event Bus & Sync Primitives

Foundation for all inter-task communication. Three queues + two mutexes, statically allocated in [Queues.cpp](/home/bitbyte08/Documents/Door.dot/src/core/Queues.cpp), initialized once from `setup()` before any task starts.

## Queue Routing

| Queue | Size | Producer(s) | Consumer | Sink helper |
|-------|------|-------------|----------|-------------|
| `eventQueue` | 10 | `QRScannerTask`, `NetworkTask`, `MQTTClient` (callback) | `StateManagerTask` | `Queues::toState(e)` |
| `renderQueue` | 16 | `StateManagerTask`, `NetworkTask`, `LockTask`, `NetworkManager` | `RenderTask` | `Queues::toRender(e)` |
| `networkQueue` | 8 | reserved | unused | `Queues::toNetwork(e)` |

Sizes live in [config/pins.h](/home/bitbyte08/Documents/Door.dot/src/config/pins.h) (`*_QUEUE_SIZE`). Default send timeout is 100 ms; default recv is `portMAX_DELAY` (blocking).

## Event Discipline

- `Event` is a POD with a tagged `union` of variant payloads. `sizeof(Event)` is bounded by the largest variant (`qr.code[64]`). Total queue memory ≈ `34 × sizeof(Event)`.
- **Always use `makeXxxEvent(...)` builders.** They zero-init via `Event{}` and set `timestamp = millis()`. Hand-rolling an `Event` literal leaves the union indeterminate.
- **Strings are fixed-size.** Builders `strncpy` into `code[64]`, `userName[32]`, `command[16]`, `roomCode[32]`, `message[48]`, with `sizeof(dst) - 1` to leave the null. Match this idiom when adding new variants.
- **One variant per event type.** Do not access `e.data.qr` when `e.type != QR_SCANNED`. The compiler will not stop you; the bug will be silent corruption.

## Adding an Event

1. Add the case to `enum class EventType` in [Events.h](/home/bitbyte08/Documents/Door.dot/src/core/Events.h).
2. Add a `struct { ... } myVariant` to the `data` union (only if the existing variants don't fit).
3. Add a `makeMyEvent(...)` builder — start from `makeEvent(EventType::MY_TYPE)`.
4. Handle it in `StateManagerTask::handleEvent` and (if user-visible) `RenderTask::handleEvent`. The current `default: break;` will silently drop unhandled types.
5. If the producer runs in an ISR, switch the send to `xQueueSendFromISR` — `Queues::send` uses the task-context API.

## Mutexes

| Mutex | Protects | Used by |
|-------|----------|---------|
| `Mutexes::uiMutex` | NanoUI tree (theoretical) | Declared, **never taken**. Render is the sole UI writer today; if you add a second writer, wrap with `Mutexes::Lock lock(Mutexes::uiMutex)`. |
| `Mutexes::configMutex` | NVS via `Preferences` | Declared, **never taken**. Config is written from `StateManagerTask` (room code) and `NetworkManager` (WiFi/MQTT) — both on core 1, but not serialized. Take this lock if you add a third writer or call from a different core. |

The `Lock` RAII helper takes a 1 s default timeout and exposes `acquired()` — check it before acting on shared state.

## Anti-Patterns

- Do not call `xQueueCreate` outside `Queues::init()`. Late-created queues will not be visible to other translation units.
- Do not pass `Event` by pointer through `xQueueSend` — the API copies by value (`sizeof(Event)`), and pointer lifetimes don't survive the queue boundary.
- Do not use `eventQueue` from an ISR via `Queues::send`. Add a `sendFromISR` helper following the upstream FreeRTOS pattern.
- Do not expand a variant past `qr.code[64]` without auditing queue memory budget.
