import re
import logging
import requests
import hashlib
import time

from locales.texts import t
from utils import user_data as ud
# Предполагается, что вы добавите push_existing_card_menu и push_no_card_menu в utils.line_api
from utils.line_api import (
    push_text, 
    push_yes_no, 
    push_back_to_menu, 
    push_image,
    push_existing_card_menu,  # ← Новое: меню для существующей карты (Кнопки: Как использовать, Главное меню)
    push_no_card_menu        # ← Новое: меню при отсутствии карты (Кнопки: Найти магазин, Главное меню)
)
from utils.otp import generate_otp, verify_otp, send_otp_sms
from utils.odoo import register_customer
from utils.api_client import register_channel
from utils.line_registry import bind as registry_bind   
from webhook_api import flush_pending                    
from config import PIXEL_ID, ACCESS_TOKEN

logger = logging.getLogger(__name__)

PHONE_REGEX = re.compile(r"^\+?[1-9]\d{7,14}$")
META_ADS_URL = f"https://graph.facebook.com/v19.0/{PIXEL_ID}/events"


async def loyalty_start(user_id: str):
    lang = ud.get_lang(user_id)
    
    # TODO: Реализуйте проверку наличия телефона/карты у пользователя по LINE user_id.
    # Например, проверка через локальный registry или запрос в CRM Odoo.
    user_phone = None  # get_user_phone_by_line(user_id)

    if user_phone:
        # КАРТА УЖЕ ЕСТЬ
        # Отправляем сообщение "Вот твоя карта..." с кнопками "Как использовать" и "Главное меню"
        push_existing_card_menu(user_id, t(lang, "loyalty_already_have_card_text"), lang)
        
        # Если необходимо сразу приложить штрихкод, раскомментируйте (настроив получение url):
        # barcode_url = get_user_barcode_url(user_id)
        # if barcode_url:
        #     push_image(user_id, barcode_url)
    else:
        # КАРТЫ ЕЩЕ НЕТ
        # Отправляем приветственный текст "🎁 Моя карта лояльности" с кнопками "Найти магазин" и "Главное меню"
        push_no_card_menu(user_id, t(lang, "loyalty_start_no_card_text"), lang)
        
        # Сразу переводим пользователя в стейт ожидания телефона, чтобы он мог отправить его текстом
        ud.set_state(user_id, "loyalty:phone")


async def handle_loyalty_input(user_id: str, text: str):
    state = ud.get_state(user_id)
    lang = ud.get_lang(user_id)

    if state == "loyalty:phone":
        await _process_phone(user_id, text, lang)
    elif state == "loyalty:otp":
        await _process_otp(user_id, text, lang)
    elif state == "loyalty:name":
        await _process_name(user_id, text, lang)
    elif state == "loyalty:country":
        await _process_country(user_id, text, lang)
    elif state == "loyalty:tourist":
        await _process_tourist_text(user_id, text, lang)
    elif state == "loyalty:thai_citizen":
        await _process_thai_citizen_text(user_id, text, lang)


async def handle_loyalty_postback(user_id: str, data: str):
    lang = ud.get_lang(user_id)
    
    # Обработка новых интерактивных кнопок
    if data == "loyalty:how_to_use":
        push_text(user_id, t(lang, "how_to_use_loyalty"))
    elif data == "loyalty:find_store":
        # Шаблон обработки или вызова локации/карты магазинов
        push_text(user_id, t(lang, "find_store_instruction"))
        
    # Базовый флоу регистрации
    elif data == "tourist:yes":
        await _tourist_answer(user_id, True, lang)
    elif data == "tourist:no":
        await _tourist_answer(user_id, False, lang)
    elif data == "thai_citizen:yes":
        await _thai_citizen_answer(user_id, True, lang)
    elif data == "thai_citizen:no":
        await _thai_citizen_answer(user_id, False, lang)


# ── Шаг 1: телефон ─────────────────────────────────────────────────────────

async def _process_phone(user_id: str, phone_raw: str, lang: str):
    phone = phone_raw.strip().replace(" ", "").replace("-", "")

    if not PHONE_REGEX.match(phone):
        push_text(user_id, t(lang, "loyalty_phone_invalid"))
        return

    if not phone.startswith("+"):
        phone = "+" + phone

    ud.update_data(user_id, phone=phone)
    otp = generate_otp(phone)
    send_otp_sms(phone, otp)

    ud.set_state(user_id, "loyalty:otp")
    push_text(user_id, t(lang, "loyalty_otp_sent", phone=phone))


# ── Шаг 2: OTP ─────────────────────────────────────────────────────────────

async def _process_otp(user_id: str, entered: str, lang: str):
    data = ud.get_data(user_id)
    phone = data.get("phone", "")
    success, reason = verify_otp(phone, entered.strip())

    if not success:
        if reason == "too_many":
            ud.clear_state(user_id)
            push_text(user_id, t(lang, "loyalty_otp_attempts"))
        else:
            push_text(user_id, t(lang, "loyalty_otp_invalid"))
        return

    ud.set_state(user_id, "loyalty:name")
    push_text(user_id, t(lang, "loyalty_ask_name"))


# ── Шаг 3: имя ─────────────────────────────────────────────────────────────

async def _process_name(user_id: str, name: str, lang: str):
    name = name.strip()
    if len(name) < 2:
        push_text(user_id, t(lang, "loyalty_name_invalid"))
        return

    ud.update_data(user_id, name=name)
    ud.set_state(user_id, "loyalty:country")
    push_text(user_id, t(lang, "loyalty_ask_country"))


# ── Шаг 4: страна ──────────────────────────────────────────────────────────

async def _process_country(user_id: str, country: str, lang: str):
    ud.update_data(user_id, country=country.strip())
    ud.set_state(user_id, "loyalty:tourist")
    push_yes_no(user_id, t(lang, "loyalty_ask_tourist"), lang, "tourist:yes", "tourist:no")


# ── Шаг 5: турист (postback или текст) ─────────────────────────────────────

async def _process_tourist_text(user_id: str, text: str, lang: str):
    yes_words = {"yes", "да", "ใช่", "1"}
    tourist = text.strip().lower() in yes_words
    await _tourist_answer(user_id, tourist, lang)


async def _tourist_answer(user_id: str, tourist: bool, lang: str):
    ud.update_data(user_id, tourist=tourist)
    if tourist:
        ud.update_data(user_id, thai_citizen=False)
        await _finalize(user_id, lang)
    else:
        ud.set_state(user_id, "loyalty:thai_citizen")
        push_yes_no(user_id, t(lang, "loyalty_ask_thai_citizen"), lang,
                    "thai_citizen:yes", "thai_citizen:no")


# ── Шаг 6: гражданин Таиланда (postback или текст) ─────────────────────────

async def _process_thai_citizen_text(user_id: str, text: str, lang: str):
    yes_words = {"yes", "да", "ใช่", "1"}
    thai = text.strip().lower() in yes_words
    await _thai_citizen_answer(user_id, thai, lang)


async def _thai_citizen_answer(user_id: str, thai_citizen: bool, lang: str):
    ud.update_data(user_id, thai_citizen=thai_citizen)
    await _finalize(user_id, lang)


# ── Финализация: вызов Odoo API ─────────────────────────────────────────────

async def _finalize(user_id: str, lang: str):
    data = ud.get_data(user_id)
    ud.clear_state(user_id)

    phone = data.get("phone", "")
    name = data.get("name", "")
    country = data.get("country")
    tourist = data.get("tourist", False)
    thai_citizen = data.get("thai_citizen", False)

    push_text(user_id, t(lang, "loading"))

    result = register_customer(
        name=name,
        phone=phone,
        lang=lang,
        tourist=tourist,
        thai_citizen=thai_citizen,
        country=country,
        bot_platform="line",
    )

    if result is None:
        push_back_to_menu(user_id, t(lang, "loyalty_crm_error"), lang)
        return

    await register_channel(phone, user_id)
    registry_bind(phone, user_id)   
    flush_pending(phone)             

    messages = result.get("content", {}).get("messages", [])
    api_message = None
    barcode = None

    for msg in messages:
        if msg.get("type") == "text":
            api_message = msg.get("text")
        elif msg.get("type") == "image":
            barcode = msg.get("url")

    if api_message:
        # Изменено: После успешной регистрации отправляем контент с кнопкой "Как использовать" 
        # вместо стандартного дефолтного возврата в меню
        push_existing_card_menu(user_id, api_message, lang)
    if barcode:
        push_image(user_id, barcode)
    if not api_message and not barcode:
        logger.error(f"Unexpected Odoo API response: {result}")
        push_back_to_menu(user_id, t(lang, "loyalty_crm_error"), lang)

    send_meta_ads_info(phone)


def send_meta_ads_info(phone: str):
    payload = {
        "data": [
            {
                "event_name": "CompleteRegistration",
                "event_time": int(time.time()),
                "action_source": "system_generated",
                "user_data": {
                    "ph": hashlib.sha256(phone.encode()).hexdigest()
                },
            }
        ]
    }
    try:
        response = requests.post(
            META_ADS_URL,
            params={"access_token": ACCESS_TOKEN},
            json=payload,
            timeout=10,
        )
        logger.info(f"[MetaAds] Response: {response.json()}")
    except Exception as e:
        logger.error(f"[MetaAds] Failed to send event: {e}")