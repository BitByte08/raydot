# NanoUI 레퍼런스

JSON 기반 터치 UI 라이브러리 for ESP32.  
`.ui.json` 파일로 UI를 정의하면 ILI9341 디스플레이에 렌더링합니다.

> 저장소: https://github.com/bssm-oss/NanoUI

---

## 설치

`platformio.ini`에 이미 추가되어 있습니다:

```ini
lib_deps =
    https://github.com/bssm-oss/NanoUI.git
```

---

## 초기화

### SPI 모드

```cpp
#include <NanoUI.h>

NanoUI::NanoUI ui;

void setup() {
    // 핀 지정
    ui.begin(10, 9, 8, 7);  // CS, DC, RST, TOUCH_CS
    
    // 또는 기본 핀 사용 (config.h 참조)
    // ui.begin();
    
    ui.loadFromFlash(UI_JSON);
}

void loop() {
    ui.update();
}
```

### 8-bit Parallel 모드

```cpp
#include <SPI.h>
#include <NanoUI.h>

NanoUI::NanoUI ui;

void setup() {
    SPI.begin(18, 19, 23);  // SCK, MISO, MOSI
    
    // 핀 지정
    ui.beginParallel(27, 2, 4, 33,  // CS, DC, WR, RST
                     12, 13, 14, 15, // DB0-DB3
                     21, 22, 25, 26, // DB4-DB7
                     5);             // TOUCH_CS
    
    // 또는 기본 핀 사용
    // ui.beginParallel();
    
    ui.loadFromFlash(UI_JSON);
}
```

---

## 기본 핀 (config.h)

### SPI 모드

| 핀 | 기본값 |
|---|--------|
| TFT_CS | 10 |
| TFT_DC | 9 |
| TFT_RST | 8 |
| TOUCH_CS | 7 |

### Parallel 모드 (LOLIN D32)

| 핀 | 기본값 |
|---|--------|
| CS | 27 |
| DC | 2 |
| WR | 4 |
| RST | 33 |
| DB0 | 12 |
| DB1 | 13 |
| DB2 | 14 |
| DB3 | 15 |
| DB4 | 21 |
| DB5 | 22 |
| DB6 | 25 |
| DB7 | 26 |
| TOUCH_CS | 5 |
| SPI_SCK | 18 |
| SPI_MISO | 19 |
| SPI_MOSI | 23 |

### 핀 오버라이드

`platformio.ini`에서 `build_flags`로 변경:

```ini
build_flags =
    -DNANOUI_SPI_TFT_CS=5
    -DNANOUI_SPI_TFT_DC=4
```

---

## JSON UI 정의

```cpp
const char UI_JSON[] PROGMEM = R"({
  "version": "1.0",
  "display": { "width": 320, "height": 240, "rotation": 1 },
  "screens": [
    {
      "id": "main",
      "background": "#1A1A2E",
      "components": [
        {
          "type": "label",
          "id": "lbl_title",
          "x": 10, "y": 10,
          "text": "Door Control",
          "style": { "color": "#FFFFFF", "fontSize": 2 }
        },
        {
          "type": "button",
          "id": "btn_open",
          "x": 90, "y": 100, "width": 140, "height": 50,
          "label": "OPEN",
          "style": { "bg": "#00B4D8", "text": "#FFFFFF", "radius": 8 },
          "onPress": "doorOpen"
        },
        {
          "type": "toggle",
          "id": "tgl_auto",
          "x": 20, "y": 180,
          "default": false,
          "style": { "activeColor": "#07E0", "inactiveColor": "#7BEF" },
          "onChange": "autoMode"
        }
      ]
    }
  ]
})";
```

---

## 컴포넌트

### button

| 필드 | 타입 | 설명 |
|------|------|------|
| `label` | string | 버튼 텍스트 |
| `style.bg` | string | 배경색 `#RRGGBB` |
| `style.text` | string | 글자색 |
| `style.radius` | number | 모서리 반경 (기본: 4) |
| `style.fontSize` | number | 글자 크기 배율 (기본: 2) |
| `onPress` | string / object | 콜백 이름 또는 `{ "action": "navigate", "target": "screenId" }` |

### label

| 필드 | 타입 | 설명 |
|------|------|------|
| `text` | string | 텍스트 |
| `style.color` | string | 글자색 |
| `style.fontSize` | number | 글자 크기 배율 (기본: 2) |
| `style.align` | string | 정렬 `"left"`, `"center"`, `"right"` |

### toggle

| 필드 | 타입 | 설명 |
|------|------|------|
| `default` | boolean | 초기 상태 |
| `style.activeColor` | string | ON 색상 |
| `style.inactiveColor` | string | OFF 색상 |
| `onChange` | string | 콜백 이름 |

### slider

| 필드 | 타입 | 설명 |
|------|------|------|
| `min` | number | 최소값 (기본: 0) |
| `max` | number | 최대값 (기본: 100) |
| `value` | number | 초기값 |
| `onChange` | string | 콜백 이름 |

---

## API

### 초기화

```cpp
void begin();                              // SPI, 기본 핀
void begin(cs, dc, rst, touch_cs);         // SPI, 핀 지정
void beginParallel();                      // Parallel, 기본 핀
void beginParallel(cs, dc, wr, rst,        // Parallel, 핀 지정
                   d0, d1, d2, d3,
                   d4, d5, d6, d7,
                   touch_cs);
```

### JSON 로드

```cpp
bool loadFromFlash(const char* jsonStr);   // PROGMEM에서 로드
bool loadFromSD(const char* path);         // SD 카드에서 로드
```

### 화면

```cpp
void show(const char* screenId);           // 화면 전환
void back();                               // 이전 화면
```

### 이벤트

```cpp
void on(const char* name, void (*cb)(UIEvent));

// UIEvent 구조체
struct UIEvent {
    const char* id;      // 컴포넌트 ID
    int value;           // slider 값
    bool toggled;        // toggle 상태
};
```

### 런타임

```cpp
void update();                            // loop()에서 호출
void setText(const char* id, const char* text);
void setValue(const char* id, int value);
void setVisible(const char* id, bool visible);
void setEnabled(const char* id, bool enabled);
```

---

## 사용 예시

```cpp
#include <NanoUI.h>

const char UI_JSON[] PROGMEM = R"({
  "version": "1.0",
  "screens": [{
    "id": "main",
    "background": "#1A1A2E",
    "components": [
      { "type": "label", "id": "status", "x": 10, "y": 10, "text": "Closed" },
      { "type": "button", "id": "btn", "x": 90, "y": 100, "width": 140, "height": 50,
        "label": "OPEN", "onPress": "openDoor" }
    ]
  }]
})";

NanoUI::NanoUI ui;

void onOpenDoor(NanoUI::UIEvent evt) {
    Serial.println("Door opened");
    ui.setText("status", "Opened");
}

void setup() {
    Serial.begin(115200);
    ui.begin();
    ui.loadFromFlash(UI_JSON);
    ui.on("openDoor", onOpenDoor);
}

void loop() {
    ui.update();
}
```

---

## 메모리 설정

```cpp
#define MAX_COMPONENTS_PER_SCREEN 20
#define MAX_SCREENS 5
#define MAX_HISTORY_DEPTH 5
#define MAX_CALLBACKS 10
#include <NanoUI.h>
```
