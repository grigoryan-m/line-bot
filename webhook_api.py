import asyncio
import logging
import os
from datetime import datetime, timezone
from typing import Optional

from fastapi import FastAPI, HTTPException, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel, field_validator
from fastapi.middleware.cors import CORSMiddleware
from fastapi import APIRouter

logger = logging.getLogger(__name__)
router = APIRouter()

# ─── Секрет для защиты endpoint'а ─────────────────────────────────────────────
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "")

# ─── Отложенные задачи ────────────────────────────────────────────────────────
_pending: dict[str, list[dict]] = {}

# ─── Конфигурация задержек ────────────────────────────────────────────────────
# Сообщение 1: Через 10 минут (600 секунд)
THANK_YOU_DELAY = int(os.getenv("THANK_YOU_DELAY_SECONDS", str(10 * 60)))
# Сообщение 2: Через 24 часа (86400 секунд)
RETENTION_DELAY = int(os.getenv("RETENTION_DELAY_SECONDS", str(24 * 60 * 60)))

# ─── Тексты сообщений ─────────────────────────────────────────────────────────
MESSAGES = {
    "thank_you": {
        "ru": (
            "🛍 Спасибо за покупку в WeedeN 🌿!\n\n"
            "Мы тщательно отбираем каждый продукт и будем рады видеть вас снова за новым опытом и любимыми позициями. 🙏\n\n"
            "— Команда WeedeN"
        ),
        "en": (
            "🛍 Thank you for your purchase at WeedeN 🌿!\n\n"
            "We carefully select every product and look forward to seeing you again for new experiences and your favorite items. 🙏\n\n"
            "— WeedeN Team"
        ),
        "thai": (
            "🛍 ขอบคุณสำหรับการซื้อสินค้าที่ WeedeN 🌿!\n\n"
            "เราคัดสรรทุกผลิตภัณฑ์อย่างพิถีพิถัน และยินดีที่จะต้อนรับคุณอีกครั้งเพื่อสัมผัสประสบการณ์ใหม่ๆ และสินค้าที่คุณชื่นชอบ 🙏\n\n"
            "— ทีมงาน WeedeN"
        ),
    },
    "retention": {
        "ru": (
            "Спасибо за то, что вы уже попробовали продукты WeedeN! 🌿\n\n"
            "Теперь самое время открыть для себя новые фавориты — у нас как раз появились позиции, которые точно стоят второго визита. Приходите!"
        ),
        "en": (
            "Thank you for trying WeedeN products! 🌿\n\n"
            "Now is the perfect time to discover new favorites — we've just added some items that are definitely worth a second visit. Come by and check them out!"
        ),
        "thai": (
            "ขอบคุณที่ไว้วางใจเลือกใช้ผลิตภัณฑ์ของ WeedeN! 🌿\n\n"
            "ตอนนี้เป็นเวลาที่เหมาะที่สุดในการค้นหาสินค้าชิ้นโปรดใหม่ๆ เราเพิ่งมีสินค้าใหม่เข้ามาซึ่งคุ้มค่ากับการกลับมาเยี่ยมชมเป็นครั้งที่สองแน่นอน แล้วแวะมานะครับ!"
        ),
    }
}


def _build_message(msg_type: str, lang: str) -> str:
    templates = MESSAGES.get(msg_type, MESSAGES["thank_you"])
    return templates.get(lang, templates["en"])


async def _send_delayed_message(
    line_user_id: str,
    lang: str,
    msg_type: str,
    delay: int,
    order_id: Optional[str] = None
):
    """Универсальная функция для отложенной отправки сообщений."""
    if delay > 0:
        await asyncio.sleep(delay)

    from utils.line_api import push_text
    text = _build_message(msg_type, lang)

    try:
        success = push_text(line_user_id, text)
        if success:
            logger.info("Sent %s to line_user_id=%s (order=%s)", msg_type, line_user_id, order_id)
        else:
            logger.error("Failed to send %s to line_user_id=%s", msg_type, line_user_id)
    except Exception as exc:
        logger.error("Exception sending %s: %s", msg_type, exc)


async def _schedule_all_messages(line_user_id: str, lang: str, order_id: Optional[str], initial_delay: int = THANK_YOU_DELAY):
    """Планирует обе рассылки: через 10 минут и через 24 часа."""
    asyncio.create_task(
        _send_delayed_message(line_user_id, lang, "thank_you", initial_delay, order_id)
    )
    asyncio.create_task(
        _send_delayed_message(line_user_id, lang, "retention", initial_delay + (RETENTION_DELAY - THANK_YOU_DELAY), order_id)
    )


def flush_pending(phone: str) -> None:
    from utils.line_registry import get_user_id
    normalized = phone.strip().replace(" ", "").replace("-", "")
    tasks = _pending.pop(normalized, [])
    if not tasks:
        return

    line_user_id = get_user_id(normalized)
    if line_user_id is None:
        return

    for task in tasks:
        elapsed = datetime.now(tz=timezone.utc).timestamp() - task["ts"]
        remaining_thank_you = max(0, THANK_YOU_DELAY - int(elapsed))

        asyncio.create_task(
            _schedule_all_messages(line_user_id, task["lang"], task["order_id"], initial_delay=remaining_thank_you)
        )


class PurchaseWebhook(BaseModel):
    phone: str
    customer_name: str
    product_name: str
    order_id: Optional[str] = None
    lang: Optional[str] = "en"

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        cleaned = v.strip().replace(" ", "").replace("-", "")
        if not cleaned.startswith("+") or len(cleaned) < 7:
            raise ValueError("phone must be in international format")
        return cleaned

    @field_validator("lang")
    @classmethod
    def validate_lang(cls, v: str) -> str:
        return v if v in {"en", "ru", "thai"} else "en"


@router.post("/odoo/purchase")
async def odoo_purchase(
    payload: PurchaseWebhook,
    x_api_key: Optional[str] = Header(default=None, alias="X-API-Key"),
):
    if WEBHOOK_SECRET and x_api_key != WEBHOOK_SECRET:
        raise HTTPException(status_code=401, detail="Invalid or missing X-API-Key")

    from utils.line_registry import get_user_id
    line_user_id = get_user_id(payload.phone)

    if line_user_id is None:
        _pending.setdefault(payload.phone, []).append({
            "lang": payload.lang,
            "order_id": payload.order_id,
            "ts": datetime.now(tz=timezone.utc).timestamp(),
        })
        return JSONResponse(status_code=202, content={"status": "queued"})

    await _schedule_all_messages(line_user_id, payload.lang, payload.order_id)

    return JSONResponse(
        status_code=200,
        content={
            "status": "scheduled",
            "line_user_id": line_user_id,
            "messages": ["thank_you_10m", "retention_24h"]
        },
    )


@router.get("/health")
async def health():
    return {"status": "ok"}


class BroadcastRequest(BaseModel):
    text: str
    photo: str | None = None
    video: str | None = None
    lang: str | None = None
    delay: float = 0.05


@router.post("/broadcast")
async def broadcast(
    payload: BroadcastRequest,
    x_api_key: Optional[str] = Header(default=None, alias="X-API-Key"),
):
    if WEBHOOK_SECRET and x_api_key != WEBHOOK_SECRET:
        raise HTTPException(status_code=401, detail="Invalid or missing X-API-Key")

    from utils.line_registry import get_all_users
    from utils.line_api import push_text, push_image, push_video

    users = get_all_users()

    sent = 0
    failed = 0

    for user in users:

        if payload.lang and user["lang"] != payload.lang:
            continue

        try:

            ok = True

            if payload.photo:
                ok &= push_image(
                    user["line_user_id"],
                    payload.photo,
                )

            if payload.video:
                preview = payload.photo or "https://dummyimage.com/640x360/cccccc/000000.jpg&text=Video"

                ok &= push_video(
                    user["line_user_id"],
                    payload.video,
                    preview,
                )

            if payload.text:
                ok &= push_text(
                    user["line_user_id"],
                    payload.text,
                )

            if ok:
                sent += 1
            else:
                failed += 1

        except Exception:
            logger.exception(
                "Broadcast failed for %s",
                user["line_user_id"],
            )
            failed += 1

        await asyncio.sleep(payload.delay)

    return {
        "status": "done",
        "sent": sent,
        "failed": failed,
        "total": sent + failed,
    }


class BroadcastRequestList(BaseModel):
    phones: list[str]
    text: str
    photo: Optional[str] = None 
    video: Optional[str] = None  
    lang: Optional[str] = None    
    delay: float = 0.05


@router.post("/broadcastlist")
async def broadcast_list(
    payload: BroadcastRequestList,
    x_api_key: Optional[str] = Header(default=None, alias="X-API-Key"),
):
    if WEBHOOK_SECRET and x_api_key != WEBHOOK_SECRET:
        raise HTTPException(status_code=401, detail="Invalid or missing X-API-Key")

    if not payload.text.strip():
        raise HTTPException(status_code=400, detail="text must not be empty")

    from utils.line_registry import get_user_id, _registry, _normalize, _entry_lang
    from utils.line_api import push_text, push_image, push_video

    sent = 0
    failed = 0
    targets: list[str] = [] 

    for phone in payload.phones:
        normalized = _normalize(phone)
        entry = _registry.get(normalized)

        if entry is None:
            logger.warning("broadcastlist: phone not found — %s", phone)
            failed += 1
            continue

        line_user_id = get_user_id(normalized)
        if not line_user_id:
            failed += 1
            continue

        if payload.lang is not None and _entry_lang(entry) != payload.lang:
            continue

        targets.append(line_user_id)

    for line_user_id in targets:
        try:
            ok = True

            if payload.photo:
                ok &= push_image(line_user_id, payload.photo)

            if payload.video:
                preview = payload.photo or "https://dummyimage.com/640x360/cccccc/000000.jpg&text=Video"
                ok &= push_video(line_user_id, payload.video, preview)

            ok &= push_text(line_user_id, payload.text)

            if ok:
                sent += 1
                logger.info("broadcastlist: sent to line_user_id=%s", line_user_id)
            else:
                failed += 1
                logger.warning("broadcastlist: partial fail for line_user_id=%s", line_user_id)

        except Exception as exc:
            failed += 1
            logger.warning("broadcastlist: exception for line_user_id=%s — %s", line_user_id, exc)

        if payload.delay > 0:
            await asyncio.sleep(payload.delay)

    logger.info("broadcastlist: done. sent=%d failed=%d", sent, failed)

    return JSONResponse(
        status_code=200,
        content={
            "status": "done",
            "sent": sent,
            "failed": failed,
            "total": sent + failed,
        },
    )