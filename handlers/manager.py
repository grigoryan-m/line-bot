"""
Чат с менеджером: AI-ассистент + эскалация на живого менеджера.
"""
import logging
from datetime import datetime, timezone, timedelta

from config import MANAGER_LINE_USER_ID, MANAGER_WORK_START, MANAGER_WORK_END
from locales.texts import t
from utils import user_data as ud
from utils.line_api import push_text, push_manager_menu, push_back_to_menu
from utils.ai import ask_ai

logger = logging.getLogger(__name__)
TZ_OFFSET = timedelta(hours=7)  # UTC+7 Bangkok


def is_manager_online() -> bool:
    now = datetime.now(tz=timezone(TZ_OFFSET))
    return MANAGER_WORK_START <= now.hour < MANAGER_WORK_END


async def manager_start(user_id: str):
    lang = ud.get_lang(user_id)
    ud.set_state(user_id, "manager:chatting")

    if not is_manager_online():
        push_back_to_menu(user_id, t(lang, "manager_offline"), lang)
    else:
        push_manager_menu(user_id, t(lang, "manager_hello"), lang)


async def handle_manager_transfer(user_id: str):
    lang = ud.get_lang(user_id)
    push_text(user_id, t(lang, "manager_transfer"))
    await _notify_manager(user_id, "User requested human agent.", lang)
    ud.clear_state(user_id)
    push_back_to_menu(user_id, t(lang, "manager_transferred"), lang)


async def handle_manager_message(user_id: str, text: str):
    lang = ud.get_lang(user_id)

    if not is_manager_online():
        await _notify_manager(user_id, text, lang)
        ud.clear_state(user_id)
        push_back_to_menu(user_id, t(lang, "manager_left_message"), lang)
        return

    ai_response = await ask_ai(text, lang)

    if "[TRANSFER_TO_HUMAN]" in ai_response:
        push_text(user_id, t(lang, "manager_transfer"))
        await _notify_manager(user_id, text, lang)
        ud.clear_state(user_id)
        push_back_to_menu(user_id, t(lang, "manager_transferred"), lang)
    else:
        push_manager_menu(user_id, ai_response, lang)


async def _notify_manager(user_id: str, user_text: str, lang: str):
    if not MANAGER_LINE_USER_ID:
        logger.warning("MANAGER_LINE_USER_ID not set")
        return
    from utils.line_api import push_text as push
    try:
        text = (
            f"🔔 New message from user\n"
            f"User ID: {user_id} (lang: {lang})\n\n"
            f"Message:\n{user_text}"
        )
        push(MANAGER_LINE_USER_ID, text)
    except Exception as e:
        logger.error(f"Failed to notify manager: {e}")
