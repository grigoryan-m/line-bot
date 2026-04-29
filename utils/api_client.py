"""
BotsAPI client for the LINE bot.

When a user follows the bot or sends /bind <phone>,
their LINE userId is registered in BotsAPI so the API
can later push review requests to them.
"""
import logging
import httpx
import os

logger = logging.getLogger(__name__)

BOTS_API_URL = os.getenv("BOTS_API_URL", "http://localhost:8000")
BOTS_API_KEY = os.getenv("BOTS_API_KEY", "")


def _headers() -> dict:
    return {"X-API-Key": BOTS_API_KEY, "Content-Type": "application/json"}


async def register_channel(phone: str, line_user_id: str) -> bool:
    """
    Bind this LINE userId to a phone number in BotsAPI.
    Called when the user sends /bind <phone> or provides phone via loyalty flow.
    Returns True on success.
    """
    if not BOTS_API_URL or not BOTS_API_KEY:
        logger.warning("BOTS_API_URL or BOTS_API_KEY not set — skipping channel bind")
        return False

    url = f"{BOTS_API_URL.rstrip('/')}/channels/bind"
    payload = {
        "phone": phone,
        "channel_type": "line",
        "external_id": line_user_id,
    }
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(url, json=payload, headers=_headers())
        if resp.status_code in (200, 201):
            logger.info("BotsAPI: bound LINE userId=%s to phone=%s", line_user_id, phone)
            return True
        logger.warning("BotsAPI bind failed %s: %s", resp.status_code, resp.text)
        return False
    except Exception as exc:
        logger.warning("BotsAPI unreachable: %s", exc)
        return False
