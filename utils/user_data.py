"""
Хранение состояния пользователей в памяти.
Аналог aiogram FSM + get_lang/set_lang из Telegram-бота.

Для production замени на Redis или БД.
"""
from typing import Optional, Any

# {user_id: {"lang": "en", "state": "...", "data": {}}}
_users: dict[str, dict] = {}


def get_lang(user_id: str) -> str:
    return _users.get(user_id, {}).get("lang", "en")


def set_lang(user_id: str, lang: str):
    if user_id not in _users:
        _users[user_id] = {}
    _users[user_id]["lang"] = lang


def get_state(user_id: str) -> Optional[str]:
    return _users.get(user_id, {}).get("state")


def set_state(user_id: str, state: Optional[str]):
    if user_id not in _users:
        _users[user_id] = {}
    _users[user_id]["state"] = state


def get_data(user_id: str) -> dict:
    return _users.get(user_id, {}).get("data", {})


def update_data(user_id: str, **kwargs):
    if user_id not in _users:
        _users[user_id] = {}
    if "data" not in _users[user_id]:
        _users[user_id]["data"] = {}
    _users[user_id]["data"].update(kwargs)


def clear_state(user_id: str):
    if user_id in _users:
        _users[user_id]["state"] = None
        _users[user_id]["data"] = {}


def clear_all(user_id: str):
    _users.pop(user_id, None)
