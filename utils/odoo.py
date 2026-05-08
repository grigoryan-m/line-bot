import os
import logging
import httpx
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

_PLATFORM_MAP = {"telegram", "whatsapp", "line"}
_LANG_MAP = {"en": "eng", "ru": "ru", "thai": "thai"}


def register_customer(
    name: str,
    phone: str,
    lang: str,
    tourist: bool,
    thai_citizen: bool,
    country: Optional[str] = None,
    email: Optional[str] = None,
    bot_platform: str = "telegram",
) -> Optional[Dict[str, Any]]:
    api_lang = _LANG_MAP.get(lang, "eng")
    if bot_platform not in _PLATFORM_MAP:
        bot_platform = "telegram"

    payload: Dict[str, Any] = {
        "name": name,
        "phone": phone,
        "bot_platform": bot_platform,
        "lang": api_lang,
        "tourist": tourist,
        "thai_citizen": thai_citizen,
    }
    if country:
        payload["country"] = country
    if email:
        payload["email"] = email

    endpoint = f"{os.getenv('ODOO_URL', '')}/api/client/register"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {os.getenv('ODOO_API_TOKEN', '')}",
    }

    try:
        with httpx.Client(timeout=15.0) as client:
            response = client.post(endpoint, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as e:
        logger.error(
            f"Odoo API HTTP error {e.response.status_code}: {e.response.text}"
        )
        return None
    except httpx.RequestError as e:
        logger.error(f"Odoo API request error: {e}")
        return None
    except Exception as e:
        logger.error(f"Odoo register_customer unexpected error: {e}")
        return None