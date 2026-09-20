import ssl
from email.message import EmailMessage
from email.utils import formataddr

import aiosmtplib

from app.config import settings


async def send_email(to: str, subject: str, body: str) -> bool:
    """Send an email through the configured SMTP server."""
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

    except Exception as e:
        print(f"[EMAIL-ERROR] {type(e).__name__}: {e}")
        return False


async def send_verification_email(to: str, token: str) -> bool:
    subject = "FDQ95 - Verify your email"
    link = f"https://fdq95.com/verify-email?token={token}"
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


# ================================================================
# ★ 好友申请邮件（修改正文，链接指向 /friends）
# ================================================================
async def send_friend_request_email(
    to: str,
    from_user_id: str,
    from_user_name: str,
    target_user_id: str,
) -> bool:
    """发送好友申请邮件。收件人登录后可在 /friends 页面接受或拒绝。"""
    subject = f"FDQ95 - {from_user_name} wants to be your friend"
    link = "https://fdq95.com/friends"
    body = (
        f"Hi,\n\n"
        f"FDQ95 user @{from_user_id} ({from_user_name}) sent you a friend request.\n\n"
        f"Please log in to FDQ95 and visit the link below to review and accept:\n"
        f"{link}\n\n"
        f"If you don't know this person, please ignore this email.\n\n"
        f"- FDQ95 Team\n"
    )
    return await send_email(to, subject, body)


# ================================================================
# ★ 新增：好友申请被接受的通知邮件
# ================================================================
async def send_friend_accepted_email(
    to: str,
    accepter_user_id: str,
    accepter_user_name: str,
) -> bool:
    """通知请求者：对方已同意好友申请。"""
    subject = f"FDQ95 - {accepter_user_name} accepted your friend request"
    link = f"https://fdq95.com/profile/{accepter_user_id}"
    body = (
        f"Great news!\n\n"
        f"FDQ95 user @{accepter_user_id} ({accepter_user_name}) has accepted "
        f"your friend request.\n\n"
        f"You can now visit their profile:\n"
        f"{link}\n\n"
        f"- FDQ95 Team\n"
    )
    return await send_email(to, subject, body)


# ================================================================
# ★ 新增：好友申请被拒绝的通知邮件
# ================================================================
async def send_friend_rejected_email(
    to: str,
    rejecter_user_id: str,
    rejecter_user_name: str,
) -> bool:
    """通知请求者：对方拒绝了你的好友申请。"""
    subject = f"FDQ95 - {rejecter_user_name} declined your friend request"
    body = (
        f"Hi,\n\n"
        f"We're sorry to inform you that FDQ95 user @{rejecter_user_id} "
        f"({rejecter_user_name}) has declined your friend request.\n\n"
        f"You can continue to explore FDQ95 and send requests to other users.\n\n"
        f"- FDQ95 Team\n"
    )
    return await send_email(to, subject, body)