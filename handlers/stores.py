"""
Поиск ближайших магазинов — геолокация или выбор региона.
"""
from locales.texts import t
from utils import user_data as ud
from utils import stores as store_utils
from utils.line_api import (
    push_text, push_location_request, push_regions,
    push_store_card, push_back_to_menu, push_main_menu
)


async def stores_start(user_id: str):
    lang = ud.get_lang(user_id)
    ud.set_state(user_id, "stores:waiting_geo")
    push_location_request(user_id, t(lang, "stores_request_geo"), lang)


async def handle_location(user_id: str, lat: float, lon: float):
    lang = ud.get_lang(user_id)
    found = store_utils.find_stores_by_location(lat, lon)
    ud.clear_state(user_id)
    await _send_store_results(user_id, found, lang)


async def handle_choose_region(user_id: str):
    lang = ud.get_lang(user_id)
    ud.set_state(user_id, "stores:choosing_region")
    regions = store_utils.get_all_regions()
    push_regions(user_id, t(lang, "stores_choose_region"), lang, regions)


async def handle_region_select(user_id: str, region: str):
    lang = ud.get_lang(user_id)
    found = store_utils.find_stores_by_region(region)
    ud.clear_state(user_id)
    await _send_store_results(user_id, found, lang)


async def _send_store_results(user_id: str, stores: list, lang: str):
    if not stores:
        push_back_to_menu(user_id, t(lang, "stores_not_found"), lang)
        return

    push_text(user_id, t(lang, "stores_result", count=len(stores)))
    for store in stores:
        push_store_card(user_id, store, lang)

    push_main_menu(user_id, t(lang, "main_menu"), lang)
