import hmac
import hashlib
import time

from config import settings


def generate_qr_code(user_id: int, seat_id: int) -> str:
    """Generate a signed QR code string: USER:{userId}:{seatId}:{timestamp}:{signature}"""
    timestamp = int(time.time())
    message = f"{user_id}:{seat_id}:{timestamp}"
    signature = hmac.new(
        settings.SECRET_KEY.encode("utf-8"),
        message.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return f"USER:{user_id}:{seat_id}:{timestamp}:{signature}"


def verify_qr_signature(qr_code: str) -> dict:
    """Verify a QR code string's HMAC signature.
    Returns dict with valid, user_id, seat_id, timestamp or valid=False."""
    try:
        parts = qr_code.split(":")
        if len(parts) != 5 or parts[0] != "USER":
            return {"valid": False, "error": "Invalid format"}

        user_id = int(parts[1])
        seat_id = int(parts[2])
        timestamp = int(parts[3])
        signature = parts[4]

        message = f"{user_id}:{seat_id}:{timestamp}"
        expected_sig = hmac.new(
            settings.SECRET_KEY.encode("utf-8"),
            message.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        if not hmac.compare_digest(signature, expected_sig):
            return {"valid": False, "error": "Invalid signature"}

        return {
            "valid": True,
            "user_id": user_id,
            "seat_id": seat_id,
            "timestamp": timestamp,
        }
    except (ValueError, IndexError):
        return {"valid": False, "error": "Parse error"}
