"""
Handler: Help — AI chat powered by Gemini.
Users enter a free-form chat with Gemini 2.5 Flash.
Under each AI reply a 'Contact manager' button is shown.
"""
import logging
from locales.texts import t
from utils import user_data as ud
from utils.gemini import ask_gemini
from utils.line_api import push_text, push_quick_reply, push_ai_response, push_back_to_menu

logger = logging.getLogger(__name__)

HELP_STATE = "help:chatting"


async def help_start(user_id: str):
    """Entry point — show welcome message and enter chat state."""
    lang = ud.get_lang(user_id)
    ud.set_state(user_id, HELP_STATE)
    ud.set_data(user_id, "gemini_history", [])

    welcome = t(lang, "help_welcome")
    push_ai_response(user_id, welcome, lang)


async def handle_help_message(user_id: str, text: str):
    """Process a user message inside the Gemini help chat."""
    lang = ud.get_lang(user_id)

    push_text(user_id, t(lang, "loading"))

    history = ud.get_data(user_id, "gemini_history") or []

    reply = await ask_gemini(user_message=text, conversation_history=history)

    history.append({"role": "user", "text": text})
    history.append({"role": "model", "text": reply})
    if len(history) > 20:
        history = history[-20:]
    ud.set_data(user_id, "gemini_history", history)

    push_ai_response(user_id, reply, lang)


async def handle_contact_manager(user_id: str):
    """User tapped 'Contact manager' under an AI reply — show manager LINE ID."""
    import os
    lang = ud.get_lang(user_id)
    manager_line_id = os.getenv("MANAGER_LINE_ID", "")

    if manager_line_id:
        text = t(lang, "manager_username_prompt").format(line_id=manager_line_id)
    else:
        text = t(lang, "manager_transferred")

    ud.set_state(user_id, None)
    push_back_to_menu(user_id, text, lang)
