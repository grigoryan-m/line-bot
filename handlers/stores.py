"""
Хендлер поиска магазинов — полный аналог Telegram-версии handlers/stores.py.

Поддерживает:
  - Поиск по геолокации (ближайшие магазины в радиусе 3 км)
  - Поиск по региону
  - Вывод карточек магазинов со ссылкой на Google Maps
"""
import math
import json
import os
import logging

from locales.texts import t
from utils import user_data as ud
from utils.line_api import (
    push_text,
    push_back_to_menu,
    push_location_request,
    push_regions,
    push_messages,
    _send,
)

logger = logging.getLogger(__name__)

STORES_FILE = os.path.join(os.path.dirname(__file__), "../data/stores.json")
SEARCH_RADIUS_KM = 3.0

LINE_PUSH_URL = "https://api.line.me/v2/bot/message/push"


# ── Утилиты ────────────────────────────────────────────────────────────────

def _haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _load_stores():
    try:
        with open(STORES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []


def find_stores_by_location(lat, lon, radius_km=SEARCH_RADIUS_KM):
    stores = _load_stores()
    results = []
    for store in stores:
        s_lat, s_lon = store.get("lat"), store.get("lon")
        if s_lat is not None and s_lon is not None:
            dist = _haversine(lat, lon, float(s_lat), float(s_lon))
            if dist <= radius_km:
                copy = store.copy()
                copy["distance_km"] = round(dist, 2)
                results.append(copy)
    results.sort(key=lambda x: x["distance_km"])
    return results[:5]


def find_stores_by_region(region):
    stores = _load_stores()
    return [s for s in stores if region.lower() in s.get("region", "").lower()][:5]


def _get_unique_regions():
    stores = _load_stores()
    seen = []
    for s in stores:
        r = s.get("region", "").strip()
        if r and r not in seen:
            seen.append(r)
    return seen


# ── Отправка карточки магазина со ссылкой ──────────────────────────────────

def _push_store_card(user_id: str, store: dict, lang: str) -> bool:
    """
    Карточка магазина в виде Flex Message с кнопкой-ссылкой на Google Maps.
    Аналог Telegram-функции store_maps_button — выводит имя, адрес, часы,
    расстояние (если есть) и кнопку «Открыть в Google Maps».
    """
    maps_url = (
        store.get("google_maps_url")
        or f"https://www.google.com/maps?q={store['lat']},{store['lon']}"
    )

    name = store.get("name", "—")
    address = store.get("address", "—")
    hours = store.get("hours")
    dist = store.get("distance_km")

    # Строим текстовые строки карточки
    contents = [
        {
            "type": "text",
            "text": f"🏪 {name}",
            "weight": "bold",
            "size": "md",
            "wrap": True,
        },
        {
            "type": "text",
            "text": f"📍 {address}",
            "size": "sm",
            "color": "#555555",
            "wrap": True,
        },
    ]

    if hours:
        contents.append({
            "type": "text",
            "text": f"🕐 {hours}",
            "size": "sm",
            "color": "#555555",
        })

    if dist is not None:
        contents.append({
            "type": "text",
            "text": f"📏 {dist} km",
            "size": "sm",
            "color": "#888888",
        })

    flex = {
        "type": "bubble",
        "body": {
            "type": "box",
            "layout": "vertical",
            "spacing": "sm",
            "contents": contents,
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "button",
                    "action": {
                        "type": "uri",
                        "label": t(lang, "btn_open_maps"),
                        "uri": maps_url,
                    },
                    "style": "primary",
                    "height": "sm",
                }
            ],
        },
    }

    return _send(LINE_PUSH_URL, {
        "to": user_id,
        "messages": [{
            "type": "flex",
            "altText": f"🏪 {name} — {t(lang, 'btn_open_maps')}",
            "contents": flex,
        }],
    })


# ── Хендлеры ───────────────────────────────────────────────────────────────

async def stores_start(user_id: str):
    """Начало флоу поиска магазинов — запрашиваем геолокацию или регион."""
    lang = ud.get_lang(user_id)
    ud.set_state(user_id, "stores:waiting_geo")
    push_location_request(user_id, t(lang, "stores_request_geo"), lang)


async def handle_location(user_id: str, lat: float, lon: float):
    """Пользователь отправил геолокацию — ищем ближайшие магазины."""
    lang = ud.get_lang(user_id)
    ud.set_state(user_id, None)

    stores = find_stores_by_location(lat, lon)

    if not stores:
        push_back_to_menu(user_id, t(lang, "stores_not_found"), lang)
        return

    push_text(user_id, t(lang, "stores_result", count=len(stores)))
    for store in stores:
        _push_store_card(user_id, store, lang)


async def handle_choose_region(user_id: str):
    """Пользователь нажал «Выбрать регион» — показываем список регионов."""
    lang = ud.get_lang(user_id)
    ud.set_state(user_id, "stores:choosing_region")
    regions = _get_unique_regions()
    push_regions(user_id, t(lang, "stores_choose_region"), lang, regions)


async def handle_region_select(user_id: str, region: str):
    """Пользователь выбрал регион — показываем магазины региона."""
    lang = ud.get_lang(user_id)
    ud.set_state(user_id, None)

    stores = find_stores_by_region(region)

    if not stores:
        push_back_to_menu(user_id, t(lang, "stores_not_found"), lang)
        return

    push_text(user_id, t(lang, "stores_result", count=len(stores)))
    for store in stores:
        _push_store_card(user_id, store, lang)
