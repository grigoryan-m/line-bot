from config import SOCIALS_URL
from locales.texts import t
from utils import user_data as ud
from utils.line_api import _send, LINE_PUSH_URL, HEADERS


async def handle_socials(user_id: str):
    lang = ud.get_lang(user_id)
    from locales.texts import t as _t
    _send(LINE_PUSH_URL, {
        "to": user_id,
        "messages": [{
            "type": "text",
            "text": _t(lang, "socials_text"),
            "quickReply": {
                "items": [
                    {
                        "type": "action",
                        "action": {"type": "uri", "label": _t(lang, "btn_open_socials"), "uri": SOCIALS_URL}
                    },
                    {
                        "type": "action",
                        "action": {
                            "type": "postback",
                            "label": _t(lang, "btn_main_menu"),
                            "data": "menu:main",
                            "displayText": _t(lang, "btn_main_menu"),
                        }
                    },
                ]
            }
        }]
    })
