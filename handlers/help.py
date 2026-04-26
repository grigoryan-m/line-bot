"""
Handler: Help — AI chat powered by Gemini.
Users enter a free-form chat with Gemini 2.5 Flash.
"""
import logging
from locales.texts import t
from utils import user_data as ud
from utils.gemini import ask_gemini
from utils.line_api import push_text, push_quick_reply

logger = logging.getLogger(__name__)

HELP_STATE = "help:chatting"


async def help_start(user_id: str):
    """Entry point — show welcome message and enter chat state."""
    lang = ud.get_lang(user_id)
    ud.set_state(user_id, HELP_STATE)
    # Clear any existing conversation history for this session
    ud.set_data(user_id, "gemini_history", [])

    welcome = t(lang, "help_welcome")
    _push_help_message(user_id, welcome, lang)


async def handle_help_message(user_id: str, text: str):
    """Process a user message inside the Gemini help chat."""
    lang = ud.get_lang(user_id)

    # Show typing indicator text (optional friendliness)
    push_text(user_id, t(lang, "loading"))

    # Load conversation history
    history = ud.get_data(user_id, "gemini_history") or []

    # Call Gemini
    reply = await ask_gemini(user_message=text, conversation_history=history)

    # Update history (keep last 10 turns to avoid context bloat)
    history.append({"role": "user", "text": text})
    history.append({"role": "model", "text": reply})
    if len(history) > 20:  # 10 user + 10 model turns
        history = history[-20:]
    ud.set_data(user_id, "gemini_history", history)

    _push_help_message(user_id, reply, lang)


def _push_help_message(user_id: str, text: str, lang: str):
    """Send a message with persistent help-chat action buttons."""
    push_quick_reply(user_id, text, [
        (t(lang, "btn_help_new_chat"), "help:new_chat"),
        (t(lang, "btn_main_menu"), "menu:main"),
    ])
