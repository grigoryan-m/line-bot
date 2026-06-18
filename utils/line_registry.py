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
from typing import Optional

logger = logging.getLogger(__name__)

_REGISTRY_PATH = os.path.join(os.path.dirname(__file__), "../data/line_registry.json")

# In-memory кэш: { "normalized_phone": "Uxxxxxxxxx..." }
_registry: dict[str, str] = {}


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


def bind(phone: str, line_user_id: str) -> None:
    """Привязывает номер телефона к LINE userId."""
    key = _normalize(phone)
    _registry[key] = line_user_id
    _save()
    logger.info("line_registry: bound phone=%s → line_user_id=%s", key, line_user_id)


def get_user_id(phone: str) -> Optional[str]:
    """Возвращает LINE userId по номеру телефона или None."""
    return _registry.get(_normalize(phone))


def get_phone(line_user_id: str) -> Optional[str]:
    """Возвращает номер телефона по LINE userId или None (обратный поиск)."""
    for phone, uid in _registry.items():
        if uid == line_user_id:
            return phone
    return None


# Загружаем при импорте модуля
_load()
