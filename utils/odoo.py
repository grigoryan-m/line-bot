import os
import logging
import httpx
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

_PLATFORM_MAP = {"telegram", "whatsapp", "line"}
_LANG_MAP = {"en": "eng", "ru": "ru", "thai": "thai"}


def get_loyalty_card(phone: str, lang: str) -> Optional[Dict[str, Any]]:
    """
    Получает данные существующей карты лояльности по номеру телефона.
    Использует идемпотентный эндпоинт /api/client/register — он возвращает
    карту если клиент уже есть, либо создаёт новую запись.
    Возвращает тот же формат (messages с text + image).
    """
    api_lang = _LANG_MAP.get(lang, "eng")
    endpoint = f"{os.getenv('ODOO_URL', '')}/api/client/register"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {os.getenv('ODOO_API_TOKEN', '')}",
        "X-Odoo-Database": f"{os.getenv('ODOO_HEADER', '')}",
    }
    payload = {
        "phone": phone,
        "lang": api_lang,
        "bot_platform": "line",
    }

    try:
        with httpx.Client(timeout=15.0) as client:
            response = client.post(endpoint, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as e:
        logger.error(
            f"Odoo get_loyalty_card HTTP error {e.response.status_code}: {e.response.text}"
        )
        return None
    except httpx.RequestError as e:
        logger.error(f"Odoo get_loyalty_card request error: {e}")
        return None
    except Exception as e:
        logger.error(f"Odoo get_loyalty_card unexpected error: {e}")
        return None


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
        "X-Odoo-Database": f"{os.getenv('ODOO_HEADER', '')}",
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