import os
from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://fdq95:fdq95_secret@db:5432/fdq95_db",
    )
    SECRET_KEY: str = os.getenv(
        "SECRET_KEY", "change-me-to-a-long-random-string"
    )
    CORS_ORIGINS: str = os.getenv("CORS_ORIGINS", "*")

    LIBRETRANSLATE_URL: str = os.getenv(
        "LIBRETRANSLATE_URL", "http://libretranslate:5000"
    )
    LIBRETRANSLATE_API_KEY: str = os.getenv("LIBRETRANSLATE_API_KEY", "")

    # ---- SMTP ----
    SMTP_HOST: str = os.getenv("SMTP_HOST", "")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587") or "587")
    # "ssl" for port 465, "starttls" for port 587, "none" for plain
    SMTP_SECURITY: str = os.getenv("SMTP_SECURITY", "starttls").lower()
    # Accept both SMTP_USERNAME (Hostinger style) and SMTP_USER (legacy)
    SMTP_USERNAME: str = os.getenv(
        "SMTP_USERNAME", os.getenv("SMTP_USER", "")
    )
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    # Accept both MAIL_FROM (Hostinger style) and SMTP_FROM (legacy)
    MAIL_FROM: str = os.getenv(
        "MAIL_FROM", os.getenv("SMTP_FROM", "")
    ) or os.getenv("SMTP_USERNAME", os.getenv("SMTP_USER", ""))

    @property
    def cors_origin_list(self) -> List[str]:
        if self.CORS_ORIGINS.strip() == "*":
            return ["*"]
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


settings = Settings()