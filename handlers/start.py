"""
Handler: Start — приветствие, выбор языка, главное меню.
Аналог handlers/start.py из Telegram-бота.
"""
import logging
from locales.texts import t
from utils import user_data as ud
from utils.line_api import push_language_select, push_main_menu, push_text, push_quick_reply
from utils.api_client import register_channel
from utils.line_registry import bind as registry_bind
from webhook_api import flush_pending

logger = logging.getLogger(__name__)


async def handle_start(user_id: str, param: str = None):
    """
    Вход в бот — аналог /start в Telegram.
    Сбрасывает состояние и показывает выбор языка.

    param — необязательный аргумент диплинка (аналог `/start <arg>` в Telegram):
      • если это телефон (начинается с '+' или состоит из цифр) —
        привязываем chat/userId к номеру в BotsAPI и отдаём pending-уведомления;
      • иначе считаем это Binom click ID, опционально с fbclid через дефис:
        "clickid-fbclid" — сохраняем для последующей отправки лида
        в Meta Ads Manager и постбэка в Binom при регистрации в loyalty.
    """
    ud.clear_state(user_id)
    lang = ud.get_lang(user_id)
    logger.info(f"[{user_id}] handle_start, lang={lang}, param={param}")

    if param:
        arg = param.strip()
        if arg.startswith("+") or arg.isdigit():
            # Телефон: начинается с + или только цифры
            phone = arg
            await register_channel(phone, user_id)
            registry_bind(phone, user_id)
            flush_pending(phone)
        else:
            # Binom click ID, опционально fbclid: "clickid-fbclid"
            parts = arg.split("-", 1)
            ud.set_binom_clickid(user_id, parts[0])
            if len(parts) > 1:
                ud.set_fbclid(user_id, parts[1])
            logger.info(f"[{user_id}] binom clickid={parts[0]} fbclid={parts[1] if len(parts) > 1 else None}")

    push_language_select(user_id)


async def handle_lang_select(user_id: str, lang: str):
    """
    Пользователь выбрал язык через postback lang:<code>.
    Аналог set_language callback в TG.
    """
    ud.set_lang(user_id, lang)
    logger.info(f"[{user_id}] language set to {lang}")

    # Подтверждение + hint лояльности
    push_text(user_id, t(lang, "lang_set"))
    push_main_menu(user_id, t(lang, "loyalty_hint"), lang)


async def handle_main_menu(user_id: str):
    """
    Показать главное меню.
    Аналог show_main_menu / back_to_menu в TG.
    """
    ud.clear_state(user_id)
    lang = ud.get_lang(user_id)
    logger.info(f"[{user_id}] handle_main_menu")
    push_main_menu(user_id, t(lang, "main_menu"), lang)
