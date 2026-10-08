"""Top-level document translation API."""

from pathlib import Path
from typing import Union
from .protector import parse_and_process_lines
from .translators.base import BaseTranslator
from .translators import get_translator

def translate_markdown(
    content: str,
    translator: Union[str, BaseTranslator] = "nllb",
    src_lang: str = "en",
    tgt_lang: str = "zh",
    max_chunk_chars: int = 400,
    **kwargs
) -> str:
    """Translates Markdown content while strictly preserving code blocks,

    formulas ($ / $$), table layouts, HTML tags, and link targets.
    """
    if isinstance(translator, str):
        engine = get_translator(translator, src_lang=src_lang, tgt_lang=tgt_lang, **kwargs)
    else:
        engine = translator

    return parse_and_process_lines(
        content=content,
        translate_fn=engine.translate,
        max_chunk_chars=max_chunk_chars
    )


def translate_file(
    input_path: Union[str, Path],
    output_path: Union[str, Path],
    translator: Union[str, BaseTranslator] = "nllb",
    src_lang: str = "en",
    tgt_lang: str = "zh",
    encoding: str = "utf-8",
    **kwargs
) -> None:
    """Translates a Markdown file and writes the result to output_path."""
    in_file = Path(input_path)
    out_file = Path(output_path)

    if not in_file.is_file():
        raise FileNotFoundError(f"Source file not found: {input_path}")

    content = in_file.read_text(encoding=encoding)
    translated_content = translate_markdown(
        content=content,
        translator=translator,
        src_lang=src_lang,
        tgt_lang=tgt_lang,
        **kwargs
    )

    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(translated_content, encoding=encoding)
