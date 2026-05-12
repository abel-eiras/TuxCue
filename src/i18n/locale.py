from __future__ import annotations

from src.i18n.strings import STRINGS, SUPPORTED_LOCALES

_current: str = "es"


def set_locale(locale: str) -> None:
    global _current
    if locale in SUPPORTED_LOCALES:
        _current = locale


def get_locale() -> str:
    return _current


def tr(key: str, **kwargs: object) -> str:
    text = STRINGS.get(_current, {}).get(key) or STRINGS["en"].get(key, key)
    return text.format(**kwargs) if kwargs else text
