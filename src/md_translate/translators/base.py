"""Base translation engine contract and registry."""

from abc import ABC, abstractmethod
from typing import Dict, Type

class BaseTranslator(ABC):
    """Abstract Base Class for translation backends."""

    def __init__(self, src_lang: str = "en", tgt_lang: str = "zh", **kwargs):
        self.src_lang = src_lang
        self.tgt_lang = tgt_lang
        self.kwargs = kwargs

    @abstractmethod
    def translate(self, text: str) -> str:
        """Translates a single segment or sentence of clean prose."""
        pass

    def warm_up(self):
        """Optional pre-loading / warming up models before batch loop."""
        pass


_TRANSLATOR_REGISTRY: Dict[str, Type[BaseTranslator]] = {}


def register_translator(name: str):
    """Decorator to register a translation backend."""
    def decorator(cls: Type[BaseTranslator]):
        _TRANSLATOR_REGISTRY[name.lower()] = cls
        return cls
    return decorator


def get_translator(name: str, src_lang: str, tgt_lang: str, **kwargs) -> BaseTranslator:
    """Factory to instantiate translation backend by name."""
    name_clean = name.lower()
    if name_clean not in _TRANSLATOR_REGISTRY:
        available = ", ".join(_TRANSLATOR_REGISTRY.keys())
        raise ValueError(f"Unknown translator '{name}'. Available translators: {available}")
    return _TRANSLATOR_REGISTRY[name_clean](src_lang=src_lang, tgt_lang=tgt_lang, **kwargs)
