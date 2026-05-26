# src/network — WiFi, AP Provisioning & MQTT

Two singletons, both driven from `NetworkTask` (100 ms tick). `NetworkManager` owns WiFi STA + AP-mode captive web setup. `MQTTClient` owns PubSubClient + topic conventions.

## NetworkManager

Boots into one of two modes based on persisted config:

| Condition | Mode | Behavior |
|-----------|------|----------|
| `wifiSSID` empty in NVS | AP | `WIFI_AP`, SSID `DoorDot-XXXX` (last 4 of MAC), password `door1234`, `WebServer` on `192.168.4.1`. Serves a single HTML form at `/`, POST to `/save` writes creds and reboots. |
| `wifiSSID` set | STA | `WiFi.begin(ssid, pass)`, up to 30 × 500 ms attempts. On failure → fall through to AP mode (so the device is always reachable). |

`update()` polls every 5 s; loss of association triggers `WiFi.reconnect()` and a `NETWORK_DISCONNECTED` render event. `NetworkTask` separately edge-detects `isConnected()` and emits to both state and render queues — `NetworkManager` itself emits only to render.

**AP-mode is full-fat HTTP.** `WebServer` is allocated with `new` and lives until `stopAPMode()`. Stay in AP until the user POSTs creds — there is no auto-timeout.

## MQTTClient

PubSubClient over a plain `WiFiClient` (no TLS). Connects with LWT `{"connected":false}` on `door/{roomCode}/status` (retained, QoS 1). Keepalive 60 s. `update()` from `NetworkTask` reconnects if `mqtt.connected() == false && network up`, then calls `mqtt.loop()`.

### Topic Layout

```
door/{roomCode}/status              # retained, periodic + LWT + lock state changes
door/{roomCode}/event               # transient events: door_open, door_close
door/{roomCode}/auth/request        # outgoing: { action, qr_code, timestamp }
door/{roomCode}/auth/response       # incoming: { success, user_name, duration }
door/{roomCode}/command             # incoming: { command: "open"|"close", param? }
```

Payloads are **hand-formatted** via `snprintf` (publish) and **hand-parsed** via `String::indexOf` (callback). ArduinoJson is on the lib_deps list but intentionally unused — match the existing style for new fields, or remove ArduinoJson from `platformio.ini` if you switch.

### Callback Threading

`PubSubClient::loop()` invokes `staticCallback` synchronously on the `NetworkTask` stack. The callback enqueues `AUTH_SUCCESS / AUTH_FAILED / COMMAND_RECEIVED` to `eventQueue`; `StateManagerTask` processes them. Do not perform UI or long work inside the callback — push an event and return.

## Anti-Patterns

- Do not call `publishX` from `StateManagerTask` and `MQTTClient` callback concurrently — they're both on core 1, but if you move callback work elsewhere, add a mutex around `mqtt.publish`.
- Do not connect MQTT before WiFi STA is associated. `connect()` returns early on `!networkManager.isConnected()`.
- Do not change `baseTopic` after `connect()` — subscriptions were issued against the old topic; the device will silently ignore commands.
- Do not increase MQTT payload buffers past 256 B without bumping PubSubClient's compile-time `MQTT_MAX_PACKET_SIZE` build flag in [platformio.ini](/home/bitbyte08/Documents/Door.dot/platformio.ini).
- Do not assume `mqtt.connected()` after a successful `connect()` — `subscribe()` can race; check `mqtt.state()` (negative = error) when debugging.
- Do not rename `apName` past 20 chars — `snprintf` truncates and the SSID will be malformed.
