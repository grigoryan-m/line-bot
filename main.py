"""
LINE Bot — главный файл FastAPI.
Вебхук принимает события LINE и маршрутизирует их в хендлеры.

Также монтирует /odoo/purchase endpoint из webhook_api.py
(точно так же, как Telegram-бот запускает webhook_api вместе с bot.py).
"""
from dotenv import load_dotenv
load_dotenv()

import hmac
import hashlib
import base64
import json
import logging
import os

from fastapi import FastAPI, Request, Header, HTTPException

import os
print("TOKEN:", repr(os.getenv("LINE_CHANNEL_ACCESS_TOKEN")))
print("TOKEN LENGTH:", len(os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "")))
print("TOKEN START:", os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "")[:20])

from fastapi import FastAPI, Request, Header, HTTPException
from contextlib import asynccontextmanager

from config import LINE_CHANNEL_SECRET
from utils import user_data as ud
from utils.api_client import register_channel

# Handlers
from handlers.start import handle_start, handle_lang_select, handle_main_menu
from handlers.loyalty import (
    loyalty_start, handle_loyalty_input, handle_loyalty_postback
)
from handlers.stores import (
    stores_start, handle_location, handle_choose_region, handle_region_select
)
from handlers.manager import (
    manager_start, handle_manager_transfer, handle_manager_message
)
from handlers.about import handle_about
from handlers.socials import handle_socials
from handlers.help import help_start, handle_help_message, handle_contact_manager

# ── Подключаем Odoo purchase webhook ──────────────────────────────────────────
# Импортируем app из webhook_api и монтируем его роуты в основной FastAPI app.
# Это аналог того, как Telegram-бот запускает webhook_api рядом с ботом.
import webhook_api as _wh_module

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="LINE Bot")

# Монтируем все роуты из webhook_api (/odoo/purchase, /health) в основной app
app.include_router(_wh_module.app.router)


# ─── Signature verification ────────────────────────────────────────────────

def verify_signature(body: bytes, signature: str) -> bool:
    import hmac, hashlib, base64
    secret = LINE_CHANNEL_SECRET
    computed = base64.b64encode(
        hmac.new(secret.encode(), body, hashlib.sha256).digest()
    ).decode()
    print("COMPUTED:", repr(computed[:20]))
    print("MATCH:", computed == signature)
    return computed == signature

# ─── Routing postback data ─────────────────────────────────────────────────

LOYALTY_STATES = {
    "loyalty:phone", "loyalty:otp", "loyalty:name",
    "loyalty:country", "loyalty:tourist", "loyalty:thai_citizen"
}
STORE_STATES = {"stores:waiting_geo", "stores:choosing_region"}
MANAGER_STATES = {"manager:chatting"}
HELP_STATES = {"help:chatting"}


async def route_postback(user_id: str, data: str):
    """Маршрутизация postback-событий (нажатия на кнопки)."""
    if data.startswith("lang:"):
        await handle_lang_select(user_id, data.split(":")[1])

    elif data == "menu:main":
        await handle_main_menu(user_id)

    elif data == "menu:stores":
        await stores_start(user_id)
    elif data == "menu:loyalty":
        await loyalty_start(user_id)
    elif data == "menu:manager":
        await manager_start(user_id)
    elif data == "menu:about":
        await handle_about(user_id)
    elif data == "menu:socials":
        await handle_socials(user_id)
    elif data == "menu:help":
        await help_start(user_id)
    elif data == "help:new_chat":
        await help_start(user_id)
    elif data == "help:contact_manager":
        await handle_contact_manager(user_id)
    elif data == "menu:lang":
        from utils.line_api import push_language_select
        push_language_select(user_id)

    elif data == "stores:choose_region":
        await handle_choose_region(user_id)
    elif data.startswith("region:"):
        region = data.split(":", 1)[1]
        await handle_region_select(user_id, region)

    elif data in {"tourist:yes", "tourist:no", "thai_citizen:yes", "thai_citizen:no"}:
        await handle_loyalty_postback(user_id, data)

    elif data == "manager:transfer":
        await handle_manager_transfer(user_id)


async def route_text(user_id: str, text: str):
    """Маршрутизация текстовых сообщений в зависимости от состояния."""
    state = ud.get_state(user_id)

    if text.strip() in {"/start", "start"}:
        await handle_start(user_id)
        return

    # /start <param>  →  диплинк с телефоном или Binom clickid-fbclid
    # (аналог `/start <arg>` в Telegram, см. handlers/start.py: handle_start)
    stripped = text.strip()
    if stripped.lower().startswith("/start ") or stripped.lower().startswith("start "):
        param = stripped.split(maxsplit=1)[1].strip()
        await handle_start(user_id, param)
        return

    if text.strip() in {"/menu", "menu"}:
        await handle_main_menu(user_id)
        return

    # /bind <phone>  →  привязать LINE userId к номеру телефона в BotsAPI
    if text.startswith("/bind"):
        parts = text.split(maxsplit=1)
        if len(parts) > 1:
            phone = parts[1].strip()
            ok = await register_channel(phone, user_id)

            # Также сохраняем в локальный реестр для Odoo webhook
            from utils.line_registry import bind as registry_bind
            from webhook_api import flush_pending
            registry_bind(phone, user_id)
            flush_pending(phone)

            from utils.line_api import push_text
            from utils.user_data import get_lang
            lang = get_lang(user_id)
            if ok:
                push_text(user_id, "✅ Ваш аккаунт привязан! Теперь мы сможем присылать вам уведомления." if lang == "ru"
                          else "✅ Account linked! We can now send you notifications.")
            else:
                push_text(user_id, "⚠️ Не удалось привязать аккаунт. Проверьте номер телефона и попробуйте снова." if lang == "ru"
                          else "⚠️ Could not link account. Please check your phone number and try again.")
        return

    if state in LOYALTY_STATES:
        await handle_loyalty_input(user_id, text)
    elif state in MANAGER_STATES:
        await handle_manager_message(user_id, text)
    elif state in HELP_STATES:
        await handle_help_message(user_id, text)
    elif state in STORE_STATES:
        lang = ud.get_lang(user_id)
        from locales.texts import t
        from utils.line_api import push_main_menu
        push_main_menu(user_id, t(lang, "main_menu"), lang)
    else:
        await handle_main_menu(user_id)


# ─── Webhook endpoint ──────────────────────────────────────────────────────

@app.post("/webhook")
async def webhook(request: Request, x_line_signature: str = Header(None)):
    body = await request.body()

    if not verify_signature(body, x_line_signature):
        raise HTTPException(status_code=400, detail="Invalid signature")

    data = json.loads(body)
    logger.info(f"Events received: {len(data.get('events', []))}")

    for event in data.get("events", []):
        event_type = event.get("type")
        source = event.get("source", {})
        user_id = source.get("userId")

        if not user_id:
            continue

        if event_type == "message":
            message = event.get("message", {})
            msg_type = message.get("type")

            if msg_type == "text":
                text = message.get("text", "").strip()
                logger.info(f"[{user_id}] text: {text}")
                await route_text(user_id, text)

            elif msg_type == "location":
                lat = message.get("latitude")
                lon = message.get("longitude")
                logger.info(f"[{user_id}] location: {lat}, {lon}")
                if lat and lon:
                    await handle_location(user_id, lat, lon)

        elif event_type == "postback":
            postback_data = event.get("postback", {}).get("data", "")
            logger.info(f"[{user_id}] postback: {postback_data}")
            await route_postback(user_id, postback_data)

        elif event_type == "follow":
            # При переходе из рекламы LINE (LINE Ads) событие follow может
            # содержать объект referral с параметром data — аналог
            # параметра диплинка `/start <arg>` в Telegram (clickid-fbclid).
            referral = event.get("referral") or {}
            referral_param = referral.get("data")
            logger.info(f"[{user_id}] new follower, referral={referral_param}")
            await handle_start(user_id, referral_param)

    return {"status": "ok"}


@app.get("/health")
async def health():
    return {"status": "ok"}
