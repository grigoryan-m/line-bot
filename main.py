"""
LINE Bot — главный файл FastAPI.
Вебхук принимает события LINE и маршрутизирует их в хендлеры.
"""
import hmac
import hashlib
import base64
import json
import logging

from fastapi import FastAPI, Request, Header, HTTPException
from contextlib import asynccontextmanager

from config import LINE_CHANNEL_SECRET
from utils import user_data as ud

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
from handlers.help import help_start, handle_help_message

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="LINE Bot")


# ─── Signature verification ────────────────────────────────────────────────

def verify_signature(body: bytes, signature: str) -> bool:
    computed = base64.b64encode(
        hmac.new(LINE_CHANNEL_SECRET.encode(), body, hashlib.sha256).digest()
    ).decode()
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
    # Выбор языка
    if data.startswith("lang:"):
        await handle_lang_select(user_id, data.split(":")[1])

    # Главное меню
    elif data == "menu:main":
        await handle_main_menu(user_id)

    # Разделы главного меню
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
    elif data == "menu:lang":
        from utils.line_api import push_language_select
        push_language_select(user_id)

    # Stores
    elif data == "stores:choose_region":
        await handle_choose_region(user_id)
    elif data.startswith("region:"):
        region = data.split(":", 1)[1]
        await handle_region_select(user_id, region)

    # Loyalty (да/нет)
    elif data in {"tourist:yes", "tourist:no", "thai_citizen:yes", "thai_citizen:no"}:
        await handle_loyalty_postback(user_id, data)

    # Manager
    elif data == "manager:transfer":
        await handle_manager_transfer(user_id)


async def route_text(user_id: str, text: str):
    """Маршрутизация текстовых сообщений в зависимости от состояния."""
    state = ud.get_state(user_id)

    # Команды
    if text.strip() in {"/start", "start"}:
        await handle_start(user_id)
        return
    if text.strip() in {"/menu", "menu"}:
        await handle_main_menu(user_id)
        return

    # FSM-состояния
    if state in LOYALTY_STATES:
        await handle_loyalty_input(user_id, text)
    elif state in MANAGER_STATES:
        await handle_manager_message(user_id, text)
    elif state in HELP_STATES:
        await handle_help_message(user_id, text)
    elif state in STORE_STATES:
        # В магазинах текст только для кнопок (регион выбирается через postback)
        # Но на случай если пользователь печатает вручную
        lang = ud.get_lang(user_id)
        from locales.texts import t
        from utils.line_api import push_main_menu
        push_main_menu(user_id, t(lang, "main_menu"), lang)
    else:
        # Нет активного состояния — показываем меню
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

        # ── Текстовое сообщение ──────────────────────────────────────────
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

        # ── Postback (нажатие кнопки) ────────────────────────────────────
        elif event_type == "postback":
            postback_data = event.get("postback", {}).get("data", "")
            logger.info(f"[{user_id}] postback: {postback_data}")
            await route_postback(user_id, postback_data)

        # ── Follow (новый подписчик) ─────────────────────────────────────
        elif event_type == "follow":
            logger.info(f"[{user_id}] new follower")
            await handle_start(user_id)

    return {"status": "ok"}


@app.get("/health")
async def health():
    return {"status": "ok"}
