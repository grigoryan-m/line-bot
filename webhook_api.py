"""
webhook_api.py
FastAPI-эндпоинт, принимающий вебхуки от Odoo CRM при покупке товара.

Полный аналог Telegram-версии webhook_api.py, адаптированный для LINE.

Запускается ВМЕСТЕ с основным LINE-ботом из main.py (оба используют
один и тот же объект FastAPI `app`, зарегистрированный в main.py).

Endpoint:
    POST /odoo/purchase
    Header: X-API-Key: <WEBHOOK_SECRET>

Payload (JSON):
{
    "phone":         "+66812345678",   // обязательно
    "customer_name": "Иван Иванов",    // обязательно
    "product_name":  "WeedeN Gold",    // обязательно
    "order_id":      "SO-1234",        // опционально, для логов
    "lang":          "ru"              // опционально, по умолчанию "en"
}

После получения:
1. Ищет LINE userId пользователя по телефону в локальном реестре.
2. Планирует отправку благодарственного сообщения через 1 час.
3. Если userId не найден — сохраняет задачу, повторит когда пользователь
   зарегистрируется через loyalty-флоу (после регистрации вызывается
   flush_pending из handlers/loyalty.py).
"""

import asyncio
import logging
import os
from datetime import datetime, timezone
from typing import Optional

from fastapi import FastAPI, HTTPException, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel, field_validator

logger = logging.getLogger(__name__)

# ─── FastAPI app ──────────────────────────────────────────────────────────────
app = FastAPI(title="WeedeN LINE Bot Webhook API", version="1.0.0")

# ─── Секрет для защиты endpoint'а (берётся из env) ───────────────────────────
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "")

# ─── Отложенные задачи для userId которые ещё не найдены ─────────────────────
# { normalized_phone: [{"lang": ..., "product_name": ..., "order_id": ..., "ts": ...}, ...] }
_pending: dict[str, list[dict]] = {}


# ─── Тексты благодарственного сообщения (идентично Telegram-версии) ───────────
_THANK_YOU: dict[str, str] = {
    "en": (
        "🛍 Thank you for purchasing {product_name}!\n\n"
        "We hope you enjoy it and look forward to seeing you again. 🙏\n\n"
        "— WeedeN team"
    ),
    "ru": (
        "🛍 Спасибо, что приобрели {product_name}!\n\n"
        "Надеемся увидеть вас ещё раз. Будем рады встрече! 🙏\n\n"
        "— Команда WeedeN"
    ),
    "thai": (
        "🛍 ขอบคุณที่ซื้อ {product_name}!\n\n"
        "หวังว่าจะได้พบคุณอีกครั้ง 🙏\n\n"
        "— ทีม WeedeN"
    ),
}

THANK_YOU_DELAY = int(os.getenv("THANK_YOU_DELAY_SECONDS", str(60 * 60)))  # 1 час


def _build_message(lang: str, product_name: str) -> str:
    template = _THANK_YOU.get(lang, _THANK_YOU["en"])
    return template.format(product_name=product_name)


async def _schedule_thank_you(
    line_user_id: str,
    lang: str,
    product_name: str,
    order_id: Optional[str],
    delay: int = THANK_YOU_DELAY,
):
    """Ждёт delay секунд, затем отправляет благодарственное сообщение через LINE push."""
    logger.info(
        "Scheduled thank-you for line_user_id=%s, product=%s, delay=%ds, order=%s",
        line_user_id, product_name, delay, order_id,
    )
    await asyncio.sleep(delay)

    # Импортируем здесь чтобы избежать circular import при старте
    from utils.line_api import push_text

    text = _build_message(lang, product_name)
    try:
        success = push_text(line_user_id, text)
        if success:
            logger.info(
                "Thank-you sent to line_user_id=%s (order=%s)", line_user_id, order_id
            )
        else:
            logger.error(
                "Failed to send thank-you to line_user_id=%s (order=%s)",
                line_user_id, order_id,
            )
    except Exception as exc:
        logger.error(
            "Exception sending thank-you to line_user_id=%s: %s", line_user_id, exc
        )


# ─── Публичная функция: вызывается из handlers/loyalty.py после регистрации ───
def flush_pending(phone: str) -> None:
    """
    Если для данного номера есть отложенные покупки (LINE userId не был известен
    в момент вебхука), запускаем задачи сейчас.
    Вызывается из loyalty.py после успешной привязки userId к телефону.
    """
    from utils.line_registry import get_user_id

    normalized = phone.strip().replace(" ", "").replace("-", "")
    tasks = _pending.pop(normalized, [])
    if not tasks:
        return

    line_user_id = get_user_id(normalized)
    if line_user_id is None:
        logger.warning("flush_pending: still no LINE userId for phone=%s", normalized)
        return

    for task in tasks:
        elapsed = datetime.now(tz=timezone.utc).timestamp() - task["ts"]
        remaining = max(0, THANK_YOU_DELAY - int(elapsed))
        asyncio.create_task(
            _schedule_thank_you(
                line_user_id,
                task["lang"],
                task["product_name"],
                task["order_id"],
                delay=remaining,
            )
        )
        logger.info(
            "flush_pending: scheduled thank-you for phone=%s, remaining=%ds",
            normalized, remaining,
        )


# ─── Pydantic модель запроса ──────────────────────────────────────────────────
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
            raise ValueError(
                "phone must be in international format, e.g. +66812345678"
            )
        return cleaned

    @field_validator("lang")
    @classmethod
    def validate_lang(cls, v: str) -> str:
        allowed = {"en", "ru", "thai"}
        return v if v in allowed else "en"


# ─── Webhook endpoint ─────────────────────────────────────────────────────────
@app.post("/odoo/purchase", summary="Odoo CRM purchase webhook")
async def odoo_purchase(
    payload: PurchaseWebhook,
    x_api_key: Optional[str] = Header(default=None, alias="X-API-Key"),
):
    # Проверка секрета
    if WEBHOOK_SECRET and x_api_key != WEBHOOK_SECRET:
        raise HTTPException(status_code=401, detail="Invalid or missing X-API-Key")

    from utils.line_registry import get_user_id

    line_user_id = get_user_id(payload.phone)

    if line_user_id is None:
        # Пользователь ещё не регистрировался через бот — сохраняем задачу
        normalized = payload.phone
        _pending.setdefault(normalized, []).append({
            "lang": payload.lang,
            "product_name": payload.product_name,
            "order_id": payload.order_id,
            "ts": datetime.now(tz=timezone.utc).timestamp(),
        })
        logger.warning(
            "odoo_purchase: no LINE userId for phone=%s — queued (order=%s)",
            payload.phone, payload.order_id,
        )
        return JSONResponse(
            status_code=202,
            content={
                "status": "queued",
                "detail": (
                    "LINE userId not found yet; "
                    "message will be sent when user registers via loyalty flow"
                ),
            },
        )

    # userId найден — планируем отправку через THANK_YOU_DELAY секунд (по умолчанию 1 час)
    asyncio.create_task(
        _schedule_thank_you(
            line_user_id,
            payload.lang,
            payload.product_name,
            payload.order_id,
            delay=THANK_YOU_DELAY,
        )
    )

    return JSONResponse(
        status_code=200,
        content={
            "status": "scheduled",
            "line_user_id": line_user_id,
            "delay_seconds": THANK_YOU_DELAY,
            "product_name": payload.product_name,
        },
    )


# ─── Health check ─────────────────────────────────────────────────────────────
@app.get("/health", summary="Health check")
async def health():
    return {"status": "ok"}
