"""
Обработчики: старт, выбор языка, главное меню.
"""
from locales.texts import t
from utils import user_data as ud
from utils.line_api import (
    push_language_select, push_main_menu, push_text
)


async def handle_start(user_id: str):
    ud.clear_state(user_id)
    push_language_select(user_id)


async def handle_lang_select(user_id: str, lang: str):
    ud.set_lang(user_id, lang)
    ud.clear_state(user_id)
    push_text(user_id, t(lang, "lang_set"))
    push_main_menu(user_id, t(lang, "main_menu"), lang)


async def handle_main_menu(user_id: str):
    lang = ud.get_lang(user_id)
    ud.clear_state(user_id)
    push_main_menu(user_id, t(lang, "main_menu"), lang)
