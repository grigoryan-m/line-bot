"""
LINE Messaging API helpers.
Заменяет aiogram — отправка сообщений, кнопок, геолокации через push/reply.
"""
import os
import requests
import logging
from typing import Optional

logger = logging.getLogger(__name__)

LINE_PUSH_URL = "https://api.line.me/v2/bot/message/push"
LINE_REPLY_URL = "https://api.line.me/v2/bot/message/reply"


def _headers() -> dict:
    """Читаем токен при каждом запросе — чтобы не зависеть от порядка импортов."""
    token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "")
    print("HEADERS TOKEN:", repr(token[:20]))  # временно
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    


def _send(url: str, payload: dict) -> bool:
    try:
        r = requests.post(url, headers=_headers(), json=payload, timeout=10)
        if r.status_code != 200:
            logger.error(f"LINE API error {r.status_code}: {r.text}")
            return False
        return True
    except Exception as e:
        logger.error(f"LINE send error: {e}")
        return False


# ─── Отправка через push (основной метод для standby-режима) ───────────────

def push_text(user_id: str, text: str) -> bool:
    return _send(LINE_PUSH_URL, {
        "to": user_id,
        "messages": [{"type": "text", "text": text}]
    })


def push_messages(user_id: str, messages: list) -> bool:
    """Отправить несколько сообщений за раз (макс 5 в LINE)."""
    for i in range(0, len(messages), 5):
        chunk = messages[i:i+5]
        _send(LINE_PUSH_URL, {"to": user_id, "messages": chunk})
    return True


def push_quick_reply(user_id: str, text: str, options: list[tuple[str, str]]) -> bool:
    """
    Quick Reply кнопки — аналог Telegram InlineKeyboard для коротких ответов.
    options: [(label, postback_data), ...]
    """
    items = [
        {
            "type": "action",
            "action": {
                "type": "postback",
                "label": label,
                "data": data,
                "displayText": label,
            }
        }
        for label, data in options
    ]
    return _send(LINE_PUSH_URL, {
        "to": user_id,
        "messages": [{
            "type": "text",
            "text": text,
            "quickReply": {"items": items}
        }]
    })


def push_button_template(user_id: str, alt_text: str, title: str, text: str, buttons: list[dict]) -> bool:
    """
    Button Template — карточка с кнопками (макс 4).
    buttons: [{"type": "postback"/"uri", "label": "...", "data"/"uri": "..."}]
    """
    return _send(LINE_PUSH_URL, {
        "to": user_id,
        "messages": [{
            "type": "template",
            "altText": alt_text,
            "template": {
                "type": "buttons",
                "title": title[:40],
                "text": text[:60],
                "actions": buttons[:4]
            }
        }]
    })


def push_main_menu(user_id: str, text: str, lang: str) -> bool:
    """
    Главное меню через Flex Message (аналог Telegram inline keyboard).
    6 кнопок, как в оригинальном боте.
    """
    from locales.texts import t

    def btn(label_key: str, data: str):
        return {
            "type": "button",
            "action": {"type": "postback", "label": t(lang, label_key)[:20], "data": data},
            "style": "secondary",
            "height": "sm",
        }

    flex = {
        "type": "bubble",
        "body": {
            "type": "box",
            "layout": "vertical",
            "spacing": "sm",
            "contents": [
                {"type": "text", "text": text, "wrap": True, "weight": "bold", "size": "md"},
                btn("btn_stores", "menu:stores"),
                btn("btn_loyalty", "menu:loyalty"),
                btn("btn_about", "menu:about"),
                btn("btn_socials", "menu:socials"),
                btn("btn_help", "menu:help"),
                btn("btn_change_lang", "menu:lang"),
            ]
        }
    }

    return _send(LINE_PUSH_URL, {
        "to": user_id,
        "messages": [{
            "type": "flex",
            "altText": text,
            "contents": flex
        }]
    })


def push_back_to_menu(user_id: str, text: str, lang: str) -> bool:
    """Текст + кнопка 'Главное меню'."""
    from locales.texts import t
    return push_quick_reply(user_id, text, [(t(lang, "btn_main_menu"), "menu:main")])


def push_language_select(user_id: str) -> bool:
    """Выбор языка через quick reply."""
    return push_quick_reply(user_id, "👋 Welcome! Please choose your language:", [
        ("🇬🇧 English", "lang:en"),
        ("🇷🇺 Русский", "lang:ru"),
        ("🇹🇭 ภาษาไทย", "lang:th"),
    ])


def push_yes_no(user_id: str, text: str, lang: str, yes_data: str, no_data: str) -> bool:
    """Да/Нет кнопки через quick reply."""
    from locales.texts import t
    return push_quick_reply(user_id, text, [
        (t(lang, "btn_yes"), yes_data),
        (t(lang, "btn_no"), no_data),
    ])


def push_location_request(user_id: str, text: str, lang: str) -> bool:
    """
    Запрос геолокации через quick reply с location action.
    """
    from locales.texts import t
    return _send(LINE_PUSH_URL, {
        "to": user_id,
        "messages": [{
            "type": "text",
            "text": text,
            "quickReply": {
                "items": [
                    {
                        "type": "action",
                        "action": {"type": "location", "label": t(lang, "btn_send_geo")}
                    },
                    {
                        "type": "action",
                        "action": {
                            "type": "postback",
                            "label": t(lang, "btn_choose_region"),
                            "data": "stores:choose_region",
                            "displayText": t(lang, "btn_choose_region"),
                        }
                    },
                    {
                        "type": "action",
                        "action": {
                            "type": "postback",
                            "label": t(lang, "btn_main_menu"),
                            "data": "menu:main",
                            "displayText": t(lang, "btn_main_menu"),
                        }
                    },
                ]
            }
        }]
    })


def push_regions(user_id: str, text: str, lang: str, regions: list[str]) -> bool:
    """Выбор региона через quick reply кнопки."""
    from locales.texts import t
    options = [(r, f"region:{r}") for r in regions[:12]]  # LINE max 13
    options.append((t(lang, "btn_back"), "menu:stores"))
    return push_quick_reply(user_id, text, options)


def push_store_card(user_id: str, store: dict, lang: str) -> bool:
    from locales.texts import t
    
    maps_url = f"https://www.google.com/maps/search/?api=1&query={store['lat']},{store['lon']}"
    
    # Тексты
    title = store["name"]
    address = f"📍 {store['address']}"
    hours = f"🕐 {store['hours']}"
    dist_text = f"📏 {store.get('distance_km')} km" if store.get('distance_km') else ""
    hint = t(lang, "show_card_hint")

    flex_contents = {
        "type": "bubble",
        "size": "mega",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "text", "text": title, "weight": "bold", "size": "xl", "wrap": True},
                {"type": "box", "layout": "vertical", "margin": "lg", "spacing": "sm", "contents": [
                    {"type": "text", "text": address, "wrap": True, "size": "sm", "color": "#666666"},
                    {"type": "text", "text": hours, "size": "sm", "color": "#666666"},
                    {"type": "text", "text": dist_text, "size": "sm", "weight": "bold", "color": "#000000"}
                ]},
                {"type": "text", "text": hint, "margin": "lg", "size": "xs", "color": "#aaaaaa", "wrap": True}
            ]
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "button",
                    "action": {
                        "type": "uri",
                        "label": t(lang, "btn_open_maps")[:20],
                        "uri": maps_url
                    },
                    "style": "primary",
                    "color": "#05c46b"
                }
            ]
        }
    }

    return _send(LINE_PUSH_URL, {
        "to": user_id,
        "messages": [
            {
                "type": "flex",
                "altText": f"Store: {title}",
                "contents": flex_contents
            }
        ]
    })

def push_manager_menu(user_id: str, text: str, lang: str) -> bool:
    """Меню чата с менеджером: кнопки 'Человек' и 'Главное меню'."""
    from locales.texts import t
    return push_quick_reply(user_id, text, [
        (t(lang, "btn_transfer_manager"), "manager:transfer"),
        (t(lang, "btn_main_menu"), "menu:main"),
    ])


def push_ai_response(user_id: str, text: str, lang: str) -> bool:
    """Ответ ИИ-ассистента с кнопкой связи с менеджером под каждым сообщением."""
    from locales.texts import t
    return push_quick_reply(user_id, text, [
        (t(lang, "btn_transfer_manager"), "help:contact_manager"),
        (t(lang, "btn_help_new_chat"), "help:new_chat"),
        (t(lang, "btn_main_menu"), "menu:main"),
    ])


def push_image(user_id: str, image_url: str) -> bool:
    return _send(LINE_PUSH_URL, {
        "to": user_id,
        "messages": [{
            "type": "image",
            "originalContentUrl": image_url,
            "previewImageUrl": image_url,
        }]
    })
