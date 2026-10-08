from .core import translate_markdown, translate_file
from .translators.base import register_translator, BaseTranslator

__version__ = "0.1.0"
__all__ = [
    "translate_markdown",
    "translate_file",
    "register_translator",
    "BaseTranslator",
]
