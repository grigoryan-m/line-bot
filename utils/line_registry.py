"""
line_registry.py
Хранит привязку phone → LINE userId.
Данные сохраняются в data/line_registry.json для переживания перезапусков.

Аналог utils/chat_registry.py из Telegram-бота, но вместо целочисленного
Telegram chat_id здесь строковый LINE userId (формат: U + 32 hex-символа).
"""

import json
import logging
import os
from typing import Any, Optional

logger = logging.getLogger(__name__)

_REGISTRY_PATH = os.path.join(os.path.dirname(__file__), "../data/line_registry.json")

# In-memory кэш: { "normalized_phone": {"user_id": "Uxxx...", "name": "John"} }
# Старые записи в формате строки поддерживаются для обратной совместимости.
_registry: dict[str, Any] = {}

# Префикс временного ключа для привязки "до регистрации" (пока не известен
# реальный номер телефона) — аналог "tg:<user_id>" в Telegram-боте.
TEMP_PREFIX = "line:"


def _normalize(phone: str) -> str:
    """Убирает пробелы и приводит к формату +XXXXXXXXXXX."""
    return phone.strip().replace(" ", "").replace("-", "")


def _load() -> None:
    """Загружает реестр с диска при старте."""
    global _registry
    try:
        os.makedirs(os.path.dirname(_REGISTRY_PATH), exist_ok=True)
        if os.path.exists(_REGISTRY_PATH):
            with open(_REGISTRY_PATH, "r", encoding="utf-8") as f:
                _registry = json.load(f)
            logger.info("line_registry: loaded %d entries", len(_registry))
    except Exception as e:
        logger.error("line_registry: load error: %s", e)
        _registry = {}


def _save() -> None:
    """Сохраняет реестр на диск."""
    try:
        os.makedirs(os.path.dirname(_REGISTRY_PATH), exist_ok=True)
        with open(_REGISTRY_PATH, "w", encoding="utf-8") as f:
            json.dump(_registry, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error("line_registry: save error: %s", e)


def _entry_user_id(entry: Any) -> Optional[str]:
    """Читает user_id из записи любого формата (строка или dict)."""
    if isinstance(entry, dict):
        return entry.get("user_id")
    return entry  # старый формат: просто строка


def _entry_name(entry: Any) -> str:
    """Читает имя из записи (пусто для старого формата)."""
    if isinstance(entry, dict):
        return entry.get("name", "")
    return ""
def _entry_lang(entry: Any) -> str:
    """Читает язык из записи (по умолчанию en)."""
    if isinstance(entry, dict):
        return entry.get("lang", "en")
    return "en"

def bind(
    phone: str,
    line_user_id: str,
    name: str = "",
    lang: str = "en",
) -> None:
    """Привязывает телефон к LINE userId, сохраняя имя."""
    key = _normalize(phone)

    # Если привязываем настоящий телефон — удаляем временную запись
    # "line:<user_id>", созданную ensure_bound() при первом контакте,
    # чтобы не оставалось двух записей на одного и того же пользователя.
    if not key.startswith(TEMP_PREFIX):
        temp_key = f"{TEMP_PREFIX}{line_user_id}"
        if temp_key != key:
            _registry.pop(temp_key, None)

    existing = _registry.get(key)
    _registry[key] = {
        "user_id": line_user_id,
        "name": name or _entry_name(existing),
        "lang": lang or _entry_lang(existing),
    }
    _save()
    logger.info("line_registry: bound phone=%s → user_id=%s name=%r", key, line_user_id, name)


def get_user_id(phone: str) -> Optional[str]:
    """Возвращает LINE userId по номеру телефона или None."""
    return _entry_user_id(_registry.get(_normalize(phone)))


def get_phone(line_user_id: str) -> Optional[str]:
    """Возвращает номер телефона по LINE userId или None (обратный поиск)."""
    for phone, entry in _registry.items():
        if _entry_user_id(entry) == line_user_id:
            return phone
    return None


def ensure_bound(user_id: str) -> None:
    """
    Гарантирует, что у LINE userId есть хоть какая-то запись в реестре.

    Если реального телефона ещё нет — привязывает временный ключ
    "line:<user_id>". Как только становится известен настоящий номер
    (см. handlers/loyalty.py: _process_phone / _finalize), bind()
    автоматически удалит временную запись и заменит её на реальную.

    Если реальный телефон уже привязан — ничего не делает.
    """
    existing = get_phone(user_id)
    if existing and not existing.startswith(TEMP_PREFIX):
        return
    bind(f"{TEMP_PREFIX}{user_id}", user_id)


def get_name(line_user_id: str) -> str:
    """Возвращает сохранённое имя пользователя по LINE userId."""
    for entry in _registry.values():
        if _entry_user_id(entry) == line_user_id:
            return _entry_name(entry)
    return ""
def get_lang(line_user_id: str) -> str:
    """Возвращает язык пользователя."""
    for entry in _registry.values():
        if _entry_user_id(entry) == line_user_id:
            return _entry_lang(entry)
    return "en"
def get_all_users() -> list[dict]:
    users = []

    for phone, entry in _registry.items():

        user_id = _entry_user_id(entry)

        if not user_id:
            continue

        users.append({
            "phone": phone,
            "line_user_id": user_id,
            "name": _entry_name(entry),
            "lang": _entry_lang(entry),
        })

    return users
    """
    Возвращает список всех зарегистрированных пользователей.

    Формат:
    [
        {
            "phone": "+1234567890",
            "line_user_id": "Uxxxxxxxx...",
            "name": "John"
        },
        ...
    ]
    """

    users = []

    for phone, entry in _registry.items():
        user_id = _entry_user_id(entry)

        if not user_id:
            continue

        users.append({
            "phone": phone,
            "line_user_id": user_id,
            "name": _entry_name(entry)
        })

    return users
# Загружаем при импорте модуля
_load()