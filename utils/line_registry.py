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


def bind(phone: str, line_user_id: str, name: str = "") -> None:
    """Привязывает телефон к LINE userId, сохраняя имя."""
    key = _normalize(phone)
    existing = _registry.get(key)
    _registry[key] = {
        "user_id": line_user_id,
        "name": name or _entry_name(existing),  # не затираем имя если уже есть
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


def get_name(line_user_id: str) -> str:
    """Возвращает сохранённое имя пользователя по LINE userId."""
    for entry in _registry.values():
        if _entry_user_id(entry) == line_user_id:
            return _entry_name(entry)
    return ""


# Загружаем при импорте модуля
_load()