import smtplib
from email.mime.text import MIMEText
from typing import Optional

from config import settings


def send_email(to: str, subject: str, body: str) -> bool:
    """Send an email via SMTP. Returns True on success.
    No-op if SMTP is not configured."""
    if not settings.SMTP_HOST:
        return False

    try:
        msg = MIMEText(body, "html")
        msg["Subject"] = subject
        msg["From"] = settings.SMTP_USER
        msg["To"] = to

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(msg)
        return True
    except Exception:
        return False
