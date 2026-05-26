#pragma once

#include <Arduino.h>

// Door.dot UI - 파란 글자
const char UI_JSON[] PROGMEM = R"({
  "version": "1.0",
  "display": { "width": 320, "height": 240, "rotation": 1 },
  "screens": [
    {
      "id": "wifi_setup",
      "background": "#000000",
      "components": [
        { "type": "label", "id": "lbl_title", "x": 0, "y": 30, "width": 320,
          "text": "WiFi Setup",
          "style": { "color": "#0000FF", "fontSize": 3, "align": "center" }
        },
        { "type": "label", "id": "lbl_ap", "x": 0, "y": 80, "width": 320,
          "text": "AP: loading...",
          "style": { "color": "#0000FF", "fontSize": 2, "align": "center" }
        },
        { "type": "label", "id": "lbl_pass", "x": 0, "y": 110, "width": 320,
          "text": "PW: door1234",
          "style": { "color": "#0000FF", "fontSize": 2, "align": "center" }
        },
        { "type": "label", "id": "lbl_url", "x": 0, "y": 150, "width": 320,
          "text": "http://192.168.4.1",
          "style": { "color": "#0000FF", "fontSize": 2, "align": "center" }
        },
        { "type": "label", "id": "lbl_hint", "x": 0, "y": 200, "width": 320,
          "text": "Connect & configure",
          "style": { "color": "#0000FF", "fontSize": 1, "align": "center" }
        }
      ]
    },
    {
      "id": "registration",
      "background": "#000000",
      "components": [
        { "type": "label", "id": "lbl_title", "x": 0, "y": 40, "width": 320,
          "text": "Room Registration",
          "style": { "color": "#0000FF", "fontSize": 2, "align": "center" }
        },
        { "type": "label", "id": "lbl_status", "x": 0, "y": 100, "width": 320,
          "text": "Scan Admin QR",
          "style": { "color": "#0000FF", "fontSize": 2, "align": "center" }
        },
        { "type": "label", "id": "lbl_hint", "x": 0, "y": 150, "width": 320,
          "text": "QR Format: ROOM:xxx",
          "style": { "color": "#0000FF", "fontSize": 1, "align": "center" }
        },
        { "type": "label", "id": "lbl_net", "x": 0, "y": 200, "width": 320,
          "text": "NET: ---",
          "style": { "color": "#0000FF", "fontSize": 1, "align": "center" }
        }
      ]
    },
    {
      "id": "registered",
      "background": "#000000",
      "components": [
        { "type": "label", "id": "lbl_title", "x": 0, "y": 60, "width": 320,
          "text": "Registered!",
          "style": { "color": "#0000FF", "fontSize": 3, "align": "center" }
        },
        { "type": "label", "id": "lbl_room", "x": 0, "y": 120, "width": 320,
          "text": "Room: ---",
          "style": { "color": "#0000FF", "fontSize": 2, "align": "center" }
        },
        { "type": "label", "id": "lbl_reboot", "x": 0, "y": 180, "width": 320,
          "text": "Rebooting...",
          "style": { "color": "#0000FF", "fontSize": 2, "align": "center" }
        }
      ]
    },
    {
      "id": "closed",
      "background": "#000000",
      "components": [
        { "type": "label", "id": "lbl_room", "x": 0, "y": 20, "width": 320,
          "text": "Room: ---",
          "style": { "color": "#0000FF", "fontSize": 2, "align": "center" }
        },
        { "type": "label", "id": "lbl_status", "x": 0, "y": 80, "width": 320,
          "text": "SCAN QR",
          "style": { "color": "#0000FF", "fontSize": 3, "align": "center" }
        },
        { "type": "label", "id": "lbl_mqtt", "x": 0, "y": 220,
          "text": "MQTT: ---",
          "style": { "color": "#0000FF", "fontSize": 1 }
        },
        { "type": "label", "id": "lbl_net", "x": 200, "y": 220,
          "text": "NET: ---",
          "style": { "color": "#0000FF", "fontSize": 1 }
        }
      ]
    },
    {
      "id": "opened",
      "background": "#000000",
      "components": [
        { "type": "label", "id": "lbl_title", "x": 0, "y": 20, "width": 320,
          "text": "OPEN",
          "style": { "color": "#0000FF", "fontSize": 4, "align": "center" }
        },
        { "type": "label", "id": "lbl_timer", "x": 0, "y": 80, "width": 320,
          "text": "5",
          "style": { "color": "#0000FF", "fontSize": 5, "align": "center" }
        },
        { "type": "label", "id": "lbl_unit", "x": 0, "y": 140, "width": 320,
          "text": "sec",
          "style": { "color": "#0000FF", "fontSize": 2, "align": "center" }
        },
        { "type": "label", "id": "lbl_user", "x": 0, "y": 200, "width": 320,
          "text": "User: ---",
          "style": { "color": "#0000FF", "fontSize": 1, "align": "center" }
        }
      ]
    },
    {
      "id": "error",
      "background": "#000000",
      "components": [
        { "type": "label", "id": "lbl_title", "x": 0, "y": 40, "width": 320,
          "text": "ERROR",
          "style": { "color": "#0000FF", "fontSize": 3, "align": "center" }
        },
        { "type": "label", "id": "lbl_error", "x": 0, "y": 100, "width": 320,
          "text": "Error Message",
          "style": { "color": "#0000FF", "fontSize": 2, "align": "center" }
        }
      ]
    }
  ]
})";
