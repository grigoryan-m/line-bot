"""
Хранение состояния пользователей в памяти.
Аналог aiogram FSM + get_lang/set_lang из Telegram-бота.

Для production замени на Redis или БД.
"""
from typing import Optional, Any

# {user_id: {"lang": "en", "state": "...", "data": {}}}
_users: dict[str, dict] = {}

# Аналог _binom_clickid / _fbclid из Telegram-бота (utils/user_data.py).
# Хранят клик-айди Binom и fbclid, полученные из параметра диплинка /start,
# до завершения регистрации в программе лояльности (отправка лида).
_binom_clickid: dict[str, str] = {}
_fbclid: dict[str, str] = {}


def get_lang(user_id: str) -> str:
    return _users.get(user_id, {}).get("lang", "en")


def set_lang(user_id: str, lang: str):
    if user_id not in _users:
        _users[user_id] = {}
    _users[user_id]["lang"] = lang


def set_binom_clickid(user_id: str, clickid: str) -> None:
    _binom_clickid[user_id] = clickid


def get_binom_clickid(user_id: str) -> Optional[str]:
    return _binom_clickid.get(user_id)


def set_fbclid(user_id: str, fbclid: str) -> None:
    _fbclid[user_id] = fbclid


def get_fbclid(user_id: str) -> Optional[str]:
    return _fbclid.get(user_id)


def get_state(user_id: str) -> Optional[str]:
    return _users.get(user_id, {}).get("state")


def set_state(user_id: str, state: Optional[str]):
    if user_id not in _users:
        _users[user_id] = {}
    _users[user_id]["state"] = state


def get_data(user_id: str, key: Optional[str] = None) -> Any:
    data = _users.get(user_id, {}).get("data", {})
    if key is not None:
        return data.get(key)
    return data


def set_data(user_id: str, key: str, value: Any):
    if user_id not in _users:
        _users[user_id] = {}
    if "data" not in _users[user_id]:
        _users[user_id]["data"] = {}
    _users[user_id]["data"][key] = value


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
