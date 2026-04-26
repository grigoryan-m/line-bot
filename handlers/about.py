from locales.texts import t
from utils import user_data as ud
from utils.line_api import push_back_to_menu


async def handle_about(user_id: str):
    lang = ud.get_lang(user_id)
    push_back_to_menu(user_id, t(lang, "about_text"), lang)
