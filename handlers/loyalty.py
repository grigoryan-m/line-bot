"""
Флоу регистрации карты лояльности — полный аналог Telegram-версии.
Состояния: loyalty:phone → loyalty:otp → loyalty:name → loyalty:country → loyalty:tourist → loyalty:thai_citizen
"""
import re
import logging

from locales.texts import t
from utils import user_data as ud
from utils.line_api import push_text, push_yes_no, push_back_to_menu, push_image
from utils.otp import generate_otp, verify_otp, send_otp_sms
from utils.odoo import register_customer

logger = logging.getLogger(__name__)

PHONE_REGEX = re.compile(r"^\+?[1-9]\d{7,14}$")


async def loyalty_start(user_id: str):
    lang = ud.get_lang(user_id)
    ud.set_state(user_id, "loyalty:phone")
    push_text(user_id, t(lang, "loyalty_start"))


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
    if data == "tourist:yes":
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
    # Quick Reply кнопки Да/Нет
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

    messages = result.get("content", {}).get("messages", [])
    api_message = None
    barcode = None

    for msg in messages:
        if msg.get("type") == "text":
            api_message = msg.get("text")
        elif msg.get("type") == "image":
            barcode = msg.get("url")

    if api_message:
        push_back_to_menu(user_id, api_message, lang)
    if barcode:
        push_image(user_id, barcode)
    if not api_message:
        logger.error(f"Unexpected Odoo API response: {result}")
        push_back_to_menu(user_id, t(lang, "loyalty_crm_error"), lang)
