import bcrypt


def hash_pin(pin: str) -> str:
    """Hash a 4-digit student PIN with bcrypt."""
    return bcrypt.hashpw(pin.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_pin(pin: str, hashed: str) -> bool:
    """Verify a 4-digit student PIN against its bcrypt hash."""
    if not hashed:
        return False
    return bcrypt.checkpw(pin.encode("utf-8"), hashed.encode("utf-8"))


def hash_admin_password(password: str) -> str:
    """Hash an admin password with bcrypt."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_admin_password(password: str, hashed: str) -> bool:
    """Verify an admin password against its bcrypt hash."""
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
