import ssl
from email.message import EmailMessage
from email.utils import formataddr

import aiosmtplib

from app.config import settings


async def send_email(to: str, subject: str, body: str) -> bool:
    """Send an email through the configured SMTP server.

    Security modes:
      - "ssl"      → implicit TLS (port 465)
      - "starttls" → upgrade after connect (port 587)
      - "none"     → plain (not recommended)
    """
    if not settings.SMTP_HOST:
        print(f"[DEV-EMAIL] To={to} Subject={subject}\n{body}")
        return True

    msg = EmailMessage()
    msg["From"] = formataddr(("FDQ95", settings.MAIL_FROM))
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(body)

    mode = settings.SMTP_SECURITY
    tls_context = ssl.create_default_context()

    try:
        if mode == "ssl":
            # Implicit TLS — used by port 465 (Hostinger default)
            await aiosmtplib.send(
                msg,
                hostname=settings.SMTP_HOST,
                port=settings.SMTP_PORT,
                username=settings.SMTP_USERNAME or None,
                password=settings.SMTP_PASSWORD or None,
                use_tls=True,
                tls_context=tls_context,
                timeout=30,
            )
        elif mode == "starttls":
            # STARTTLS — used by port 587
            await aiosmtplib.send(
                msg,
                hostname=settings.SMTP_HOST,
                port=settings.SMTP_PORT,
                username=settings.SMTP_USERNAME or None,
                password=settings.SMTP_PASSWORD or None,
                start_tls=True,
                tls_context=tls_context,
                timeout=30,
            )
        else:
            # Plain — not recommended
            await aiosmtplib.send(
                msg,
                hostname=settings.SMTP_HOST,
                port=settings.SMTP_PORT,
                username=settings.SMTP_USERNAME or None,
                password=settings.SMTP_PASSWORD or None,
                timeout=30,
            )

        print(f"[EMAIL-OK] to={to} subject={subject}")
        return True

    except Exception as e:  # noqa: BLE001
        print(f"[EMAIL-ERROR] {type(e).__name__}: {e}")
        return False


async def send_verification_email(to: str, token: str) -> bool:
    subject = "FDQ95 - Verify your email"
    link = f"https://fdq95.com/auth/verify?token={token}"
    body = (
        "Welcome to FDQ95!\n\n"
        "Please verify your email by clicking the link below:\n"
        f"{link}\n\n"
        "If you didn't sign up, please ignore this email."
    )
    return await send_email(to, subject, body)


async def send_password_reset_email(to: str, token: str) -> bool:
    subject = "FDQ95 - Reset your password"
    link = f"https://fdq95.com/reset-password?token={token}"
    body = (
        "You requested a password reset for your FDQ95 account.\n\n"
        "Click the link below to set a new password:\n"
        f"{link}\n\n"
        "If you did not request this, please ignore this email. "
        "The link expires in 1 hour."
    )
    return await send_email(to, subject, body)