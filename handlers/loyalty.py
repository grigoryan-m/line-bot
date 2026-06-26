"""
Флоу регистрации карты лояльности — полный аналог Telegram-версии.
Состояния: loyalty:phone → loyalty:otp → loyalty:name → loyalty:country → loyalty:tourist → loyalty:thai_citizen
"""
import re
import logging
import requests
import hashlib
import time

from locales.texts import t
from utils import user_data as ud
from utils.line_api import push_text, push_yes_no, push_back_to_menu, push_image
from utils.otp import generate_otp, verify_otp, send_otp_sms
from utils.odoo import register_customer, get_loyalty_card
from utils.api_client import register_channel
from utils.line_registry import bind as registry_bind, get_phone, get_name
from webhook_api import flush_pending                    # ← новое
from config import PIXEL_ID, ACCESS_TOKEN

logger = logging.getLogger(__name__)

PHONE_REGEX = re.compile(r"^\+?[1-9]\d{7,14}$")
META_ADS_URL = f"https://graph.facebook.com/v19.0/{PIXEL_ID}/events"
BINOM_POSTBACK_BASE = "https://wdn-family.com/c6ixl2k.php"


async def loyalty_start(user_id: str):
    lang = ud.get_lang(user_id)

    # Проверяем, зарегистрирован ли пользователь (есть ли привязанный телефон)
    phone = get_phone(user_id)
    if phone:
        logger.info(f"[{user_id}] already registered, phone={phone} — showing card")
        push_text(user_id, t(lang, "loading"))
        result = get_loyalty_card(phone, lang, name=get_name(user_id))

        if result is not None:
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
            if api_message or barcode:
                return

        # Если API недоступно — показываем карту из кэша или fallback
        logger.warning(f"[{user_id}] get_loyalty_card failed, starting registration flow")

    # Пользователь не зарегистрирован — запускаем флоу регистрации
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
    # otp = generate_otp(phone)
    # send_otp_sms(phone, otp)

    # ud.set_state(user_id, "loyalty:otp")
    ud.set_state(user_id, "loyalty:name")
    push_text(user_id, t(lang, "loyalty_ask_name", phone=phone))


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

    # Привязываем LINE userId к телефону в BotsAPI (для review-запросов и т.д.)
    await register_channel(phone, user_id)

    # Привязываем LINE userId к телефону локально (для Odoo purchase webhook)
    registry_bind(phone, user_id, name=name, lang=lang)  # сохраняем phone → user_id + имя

    # Отправляем отложенные purchase-уведомления, если они уже пришли от Odoo
    flush_pending(phone)             # ← новое: обрабатываем pending-очередь

    messages = result.get("content", {}).get("messages", [])
    api_message = None
    barcode = None

    for msg in messages:
        if msg.get("type") == "text":
            api_message = msg.get("text")
        elif msg.get("type") == "image":
            barcode = msg.get("url")

    # ── Lead-события: Meta Ads Manager (CAPI) + Binom postback ──────────────
    # Идентично Telegram-боту (handlers/loyalty.py): вызываются сразу после
    # успешной регистрации в Odoo, до отправки ответа пользователю.
    fbclid = ud.get_fbclid(user_id)
    send_meta_ads_info(phone, user_id, fbclid)
    fire_binom_postback(user_id)

    if api_message:
        push_back_to_menu(user_id, api_message, lang)
    if barcode:
        push_image(user_id, barcode)
    if not api_message and not barcode:
        logger.error(f"Unexpected Odoo API response: {result}")
        push_back_to_menu(user_id, t(lang, "loyalty_crm_error"), lang)


def fire_binom_postback(user_id: str):
    """Отправить постбэк в Binom об одобренной конверсии (аналог Telegram-бота)."""
    clickid = ud.get_binom_clickid(user_id)
    if not clickid:
        return
    try:
        requests.get(
            BINOM_POSTBACK_BASE,
            params={"cnv_id": clickid, "cnv_status": "approved"},
            timeout=5
        )
        logger.info(f"[binom] postback sent clickid={clickid}")
    except Exception as e:
        logger.error(f"[binom] postback error: {e}")


def send_meta_ads_info(phone: str, user_id: str = "", fbclid: str = None):
    """Send Lead event to Meta Ads Manager (CAPI). Аналог Telegram-бота."""
    user_data = {
        "ph": hashlib.sha256(phone.encode()).hexdigest(),
        "external_id": hashlib.sha256(str(user_id).encode()).hexdigest()
    }
    if fbclid:
        user_data["fbc"] = f"fb.1.{int(time.time())}.{fbclid}"

    payload = {
        "data": [
            {
                "event_name": "Lead",
                "event_time": int(time.time()),
                "action_source": "system_generated",
                "user_data": user_data
            }
        ]
    }
    try:
        response = requests.post(
            META_ADS_URL,
            params={"access_token": ACCESS_TOKEN},
            json=payload
        )
        logger.info(f"Meta Ads response: {response.json()}")
    except Exception as e:
        logger.error(f"Failed to send Meta Ads event: {e}")
