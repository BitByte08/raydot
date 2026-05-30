import smtplib
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

from config import settings


def _send_smtp(msg) -> bool:
    """Internal: send a constructed MIME message via SMTP."""
    if not settings.SMTP_HOST:
        return False
    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(msg)
        return True
    except Exception:
        return False


def send_email(to: str, subject: str, body: str) -> bool:
    """Send an HTML email via SMTP. Returns True on success.
    No-op if SMTP is not configured."""
    msg = MIMEText(body, "html")
    msg["Subject"] = subject
    msg["From"] = settings.SMTP_USER
    msg["To"] = to
    return _send_smtp(msg)


def send_email_with_image(
    to: str,
    subject: str,
    html_body: str,
    image_cid: str,
    image_bytes: bytes,
) -> bool:
    """Send an HTML email with a single inline PNG image (cid: reference).
    Use <img src="cid:IMAGE_ID" /> in html_body. IMAGE_ID should match
    the value passed as image_cid, without angle brackets.
    """
    msg = MIMEMultipart("related")
    msg["Subject"] = subject
    msg["From"] = settings.SMTP_USER
    msg["To"] = to

    msg_alt = MIMEMultipart("alternative")
    msg_alt.attach(MIMEText(html_body, "html"))
    msg.attach(msg_alt)

    img = MIMEImage(image_bytes, "png")
    img.add_header("Content-ID", f"<{image_cid}>")
    img.add_header("Content-Disposition", "inline", filename=f"{image_cid}.png")
    msg.attach(img)

    return _send_smtp(msg)
