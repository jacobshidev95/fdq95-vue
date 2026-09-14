import ssl
from email.message import EmailMessage

import aiosmtplib

from app.config import settings


async def send_email(to: str, subject: str, body: str) -> bool:
    if not settings.SMTP_HOST:
        print(f"[DEV-EMAIL] To={to} Subject={subject}\n{body}")
        return True

    msg = EmailMessage()
    msg["From"] = settings.SMTP_FROM
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(body)

    try:
        await aiosmtplib.send(
            msg,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USER or None,
            password=settings.SMTP_PASSWORD or None,
            start_tls=True,
            tls_context=ssl.create_default_context(),
        )
        return True
    except Exception as e:  # noqa: BLE001
        print(f"[EMAIL-ERROR] {e}")
        return False


async def send_verification_email(to: str, token: str) -> bool:
    subject = "FDQ95 - Verify your email"
    link = f"http://localhost:8080/auth/verify?token={token}"
    body = (
        "Welcome to FDQ95!\n\n"
        "Please verify your email by clicking the link below:\n"
        f"{link}\n\n"
        "If you didn't sign up, please ignore this email."
    )
    return await send_email(to, subject, body)
