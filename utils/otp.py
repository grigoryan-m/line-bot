import random
import logging
import time
from typing import Dict, Tuple, Optional

from twilio.rest import Client

from config import TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM_NUMBER

logger = logging.getLogger(__name__)

# In-memory OTP store: {phone: (otp, timestamp, attempts)}
_otp_store: Dict[str, Tuple[str, float, int]] = {}

OTP_TTL = 300       # 5 minutes
MAX_ATTEMPTS = 3


def generate_otp(phone: str) -> str:
    """Generate and store OTP for phone number."""
    otp = str(random.randint(100000, 999999))
    _otp_store[phone] = (otp, time.time(), 0)
    return otp


def verify_otp(phone: str, entered: str) -> Tuple[bool, str]:
    """
    Verify OTP.
    Returns (success, reason):
      reason: "ok" | "wrong" | "expired" | "too_many"
    """
    if phone not in _otp_store:
        return False, "expired"

    otp, ts, attempts = _otp_store[phone]

    if time.time() - ts > OTP_TTL:
        del _otp_store[phone]
        return False, "expired"

    if attempts >= MAX_ATTEMPTS:
        del _otp_store[phone]
        return False, "too_many"

    if entered.strip() != otp:
        _otp_store[phone] = (otp, ts, attempts + 1)
        if attempts + 1 >= MAX_ATTEMPTS:
            del _otp_store[phone]
            return False, "too_many"
        return False, "wrong"

    del _otp_store[phone]
    return True, "ok"


def send_otp_sms(phone: str, otp: str) -> bool:
    """Send OTP via Twilio SMS."""
    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        client.messages.create(
            to=phone,
            from_=TWILIO_FROM_NUMBER,
            body=f"Your verification code: {otp}. Valid for {OTP_TTL // 60} minutes.",
        )
        logger.info(f"[SMS] OTP sent to {phone}")
        return True
    except Exception as e:
        logger.error(f"[SMS] Failed to send OTP to {phone}: {e}")
        return False
