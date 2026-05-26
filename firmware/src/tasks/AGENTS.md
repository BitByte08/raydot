# src/tasks — FreeRTOS Task Layer

Header-only task subclasses. Each `*Task.h` defines a class deriving from `TaskBase` plus an `extern` instance declaration. The instances themselves are defined in [src/main.cpp](/home/bitbyte08/Documents/Door.dot/src/main.cpp) and started in `setup()` after `Queues::init()` and module `begin()` calls.

## Task Roster

| File | Class | Core | Priority | Stack | Loop Period | Consumes | Produces |
|------|-------|------|----------|-------|-------------|----------|----------|
| `StateManagerTask.h` | `StateManagerTask` | 1 | 5 | 8 KB | block on queue | `eventQueue` | `renderQueue` + direct calls to `emlockManager`, `mqttClient` |
| `RenderTask.h` | `RenderTask` | 0 | 2 | 16 KB | 33 ms (≈30 FPS) | `renderQueue` | `uiManager` (only consumer) |
| `NetworkTask.h` | `NetworkTask` | 1 | 3 | 8 KB | 100 ms | — | `eventQueue` + `renderQueue` on edge transitions |
| `QRScannerTask.h` | `QRScannerTask` | 1 | 2 | 4 KB | 50 ms | UART `Serial2` | `eventQueue` |
| `LockTask.h` | `LockTask` | 1 | 4 | 4 KB | 100 ms | `emlockManager` timer | `renderQueue` (timer ticks @ 500 ms) |

Stack sizes are `#define`d in [config/pins.h](/home/bitbyte08/Documents/Door.dot/src/config/pins.h) (`*_TASK_STACK`). Priority and core are constructor literals.

## Patterns

- **Block, don't poll.** `StateManagerTask` uses `Queues::recv(eventQueue, e)` with default `UINT32_MAX` timeout — blocks until an event arrives. All other tasks poll with `vTaskDelayUntil` at a fixed interval.
- **Edge-trigger queue sends.** `NetworkTask` only enqueues when `wifiConnected` or `mqttConnected` flips, not every tick. Follow this pattern for any new "watcher" task.
- **Render is throttled, state is reactive.** Never push the same event to `renderQueue` faster than 500 ms (see `LockTask` timer). `UIManager::setOpenTimer` also dedupes via `lastTimerValue`.
- **Cross-core split is intentional.** Only `RenderTask` lives on core 0 (paired with Arduino loop overhead and SPI). Everything else is core 1 to keep WiFi/Bluetooth interrupts away from UI. Do not move `RenderTask` to core 1 without re-measuring frame stability.
- **`task_id` lifecycle.** `TaskBase::start()` is idempotent (guards on `taskHandle != nullptr`). `stop()` calls `vTaskDelete` from outside the task — safe but the task's `run()` will not see `running = false` mid-loop unless it polls.

## Anti-Patterns

- Never call `delay(ms)` — use `delayMs(ms)` (TaskBase helper, wraps `vTaskDelay`). Plain `delay` works under Arduino but defeats FreeRTOS scheduling.
- Never re-enter `xTaskCreatePinnedToCore` for the same instance. Start is one-shot.
- Never give `StateManagerTask` a non-blocking poll — it must yield CPU when idle. The `while (running)` loop with blocking `recv` is load-bearing.
- Never publish MQTT from inside `RenderTask` or `LockTask`. MQTT is owned by `StateManagerTask` + `NetworkTask` only (so `mqtt.loop()` and publishes serialize on one core).
- Never bypass `Queues::toState()` to talk to the state machine from a task. Direct method calls on `StateManagerTask` would race the queue consumer.

## Adding a New Task

1. Pick stack size and add `#define MYTASK_STACK NNNN` to `pins.h`.
2. Create `MyTask.h` with `class MyTask : public TaskBase { ... };` + `extern MyTask myTask;` at the bottom.
3. Add the instance in [main.cpp](/home/bitbyte08/Documents/Door.dot/src/main.cpp) near the existing task globals.
4. Include the header and call `myTask.start()` in `setup()` after `Queues::init()`. Pick core 1 unless the task is UI-adjacent.
5. If the task produces a new event variant, add the enum + union member + builder in `core/Events.h` and handle it in `StateManagerTask::handleEvent` (and `RenderTask::handleEvent` if user-visible).
