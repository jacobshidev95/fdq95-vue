import os
import random

SMS_PROVIDER = os.getenv("SMS_PROVIDER", "")
SMS_API_KEY = os.getenv("SMS_API_KEY", "")

_code_store: dict[str, str] = {}


def generate_code(phone: str) -> str:
    code = f"{random.randint(100000, 999999)}"
    _code_store[phone] = code
    return code


def verify_code(phone: str, code: str) -> bool:
    return _code_store.get(phone) == code


async def send_sms_code(phone: str) -> bool:
    code = generate_code(phone)
    print(f"[SMS] Provider={SMS_PROVIDER or 'DEV'} To={phone} Code={code}")
    return True
