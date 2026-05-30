import json
import logging
from datetime import datetime, timezone

import paho.mqtt.client as mqtt

from config import settings
from database import async_session
from models.models import Room, DoorLog, QRCode, User, SeatLog
from utils.qr_signer import verify_qr_signature

from sqlalchemy import select

logger = logging.getLogger(__name__)


class MQTTService:
    """MQTT client service for communicating with firmware, kiosks, and admin."""

    def __init__(self):
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="raydot-backend")
        if settings.MQTT_USERNAME:
            self.client.username_pw_set(settings.MQTT_USERNAME, settings.MQTT_PASSWORD)
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect

    def start(self):
        """Connect to MQTT broker."""
        try:
            self.client.connect(settings.MQTT_BROKER_HOST, settings.MQTT_BROKER_PORT, 60)
            self.client.loop_start()
            logger.info("MQTT service started")
        except Exception as e:
            logger.error(f"MQTT connection failed: {e}")

    def stop(self):
        """Disconnect from MQTT broker."""
        self.client.loop_stop()
        self.client.disconnect()
        logger.info("MQTT service stopped")

    def _on_connect(self, client, userdata, flags, rc, properties=None):
        """Subscribe to all relevant topics on connect."""
        if rc == 0:
            logger.info("Connected to MQTT broker")
            # Subscribe to all door topics (wildcard)
            client.subscribe("door/+/status")
            client.subscribe("door/+/event")
            client.subscribe("door/+/auth/request")
            client.subscribe("kiosk/+/status")
            client.subscribe("kiosk/+/check-in")
            client.subscribe("kiosk/+/check-out")
            client.subscribe("kiosk/+/seat/state")
        else:
            logger.error(f"MQTT connection failed with code {rc}")

    def _on_disconnect(self, client, userdata, flags, rc, properties=None):
        """Handle disconnection."""
        logger.warning(f"MQTT disconnected with code {rc}")

    def _on_message(self, client, userdata, msg):
        """Route incoming MQTT messages to handlers."""
        topic = msg.topic
        try:
            payload = json.loads(msg.payload.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            logger.error(f"Invalid MQTT payload on {topic}")
            return

        parts = topic.split("/")
        if len(parts) < 3:
            return

        domain = parts[0]  # "door" or "kiosk"
        room_code = parts[1]
        subtopic = "/".join(parts[2:])

        if domain == "door":
            if subtopic == "status":
                self._handle_door_status(room_code, payload)
            elif subtopic == "event":
                self._handle_door_event(room_code, payload)
            elif subtopic == "auth/request":
                self._handle_auth_request(room_code, payload)
        elif domain == "kiosk":
            if subtopic == "status":
                self._handle_kiosk_status(room_code, payload)
            elif subtopic == "check-in":
                pass  # Handled via REST API
            elif subtopic == "check-out":
                pass  # Handled via REST API
            elif subtopic == "seat/state":
                self._handle_seat_state(room_code, payload)

    def _handle_door_status(self, room_code: str, payload: dict):
        """Handle door status update from firmware."""
        logger.info(f"Door status [{room_code}]: {payload}")

    def _handle_door_event(self, room_code: str, payload: dict):
        """Handle door open/close event from firmware."""
        logger.info(f"Door event [{room_code}]: {payload}")
        event_type = payload.get("type", "")
        if event_type in ("door_open", "door_close"):
            event_name = "open" if event_type == "door_open" else "close"
            # Log to DB asynchronously
            import asyncio

            async def log_event():
                async with async_session() as session:
                    result = await session.execute(select(Room).where(Room.code == room_code))
                    room = result.scalar_one_or_none()
                    if room:
                        door_log = DoorLog(room_id=room.id, event=event_name)
                        session.add(door_log)
                        await session.commit()

            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.ensure_future(log_event())
                else:
                    loop.run_until_complete(log_event())
            except Exception as e:
                logger.error(f"Failed to log door event: {e}")

    def _handle_auth_request(self, room_code: str, payload: dict):
        """Handle QR auth request from firmware.
        Firmware sends: {"action":"auth_request","qr_code":"...","timestamp":...}
        Must respond on door/{roomCode}/auth/response with:
        {"success":bool,"user_name":"str","duration":int}
        """
        qr_code = payload.get("qr_code", "")
        logger.info(f"Auth request [{room_code}]: QR={qr_code[:30]}...")

        # Verify QR code signature
        sig_result = verify_qr_signature(qr_code)
        if not sig_result.get("valid"):
            self.client.publish(
                f"door/{room_code}/auth/response",
                json.dumps({"success": False, "user_name": "", "duration": 0}),
            )
            return

        # Async DB check
        import asyncio

        async def verify_and_respond():
            async with async_session() as session:
                # Check QR record
                result = await session.execute(select(QRCode).where(QRCode.code == qr_code))
                qr = result.scalar_one_or_none()

                if not qr or qr.used:
                    self.client.publish(
                        f"door/{room_code}/auth/response",
                        json.dumps({"success": False, "user_name": "", "duration": 0}),
                    )
                    return

                now = datetime.utcnow()
                if qr.expires_at and qr.expires_at < now:
                    self.client.publish(
                        f"door/{room_code}/auth/response",
                        json.dumps({"success": False, "user_name": "", "duration": 0}),
                    )
                    return

                # Mark QR as used
                qr.used = True
                qr.used_at = now
                await session.commit()

                # Get user name
                result = await session.execute(select(User).where(User.id == qr.user_id))
                user = result.scalar_one_or_none()
                user_name = user.name if user else "Unknown"

                # Publish auth response (firmware-compatible format)
                response = {"success": True, "user_name": user_name, "duration": 5}
                self.client.publish(
                    f"door/{room_code}/auth/response",
                    json.dumps(response),
                )
                logger.info(f"Auth response [{room_code}]: success for {user_name}")

        try:
            asyncio.run(verify_and_respond())
        except Exception as e:
            logger.error(f"Auth request handling failed: {e}")
            self.client.publish(
                f"door/{room_code}/auth/response",
                json.dumps({"success": False, "user_name": "", "duration": 0}),
            )

    def _handle_kiosk_status(self, room_code: str, payload: dict):
        """Handle kiosk status update."""
        logger.info(f"Kiosk status [{room_code}]: {payload}")

    def _handle_seat_state(self, room_code: str, payload: dict):
        """Handle seat state change from kiosk."""
        logger.info(f"Seat state [{room_code}]: {payload}")

    def publish_door_command(self, room_code: str, command: str, param: int = 5):
        """Publish door command to firmware."""
        payload = json.dumps({"command": command, "param": param})
        self.client.publish(f"door/{room_code}/command", payload)
        logger.info(f"Door command [{room_code}]: {command}")

    def publish_seat_state(self, room_code: str, seat_id: int, status: str, user_id=None, user_name=None):
        """Broadcast seat state change to all kiosks."""
        payload = json.dumps({
            "seat_id": seat_id,
            "status": status,
            "user_id": user_id,
            "user_name": user_name,
        })
        self.client.publish(f"kiosk/{room_code}/seat/state", payload)

    def publish_qr_issue(self, room_code: str, qr_code: str, expires_at: str, user_id: int, seat_id: int):
        """Publish QR issuance to kiosk."""
        payload = json.dumps({
            "qr_code": qr_code,
            "expires_at": expires_at,
            "user_id": user_id,
            "seat_id": seat_id,
        })
        self.client.publish(f"kiosk/{room_code}/qr/issue", payload)


# Singleton instance
mqtt_service = MQTTService()
