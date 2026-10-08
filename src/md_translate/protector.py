"""Markdown protection and segmentation engine.

Protects code blocks, inline code, display/inline math, HTML tags, links, and tables
so translation models (NLLB, LLMs, DeepL, etc.) only translate pure prose.
"""

import re
from typing import List, Tuple

# Inline/block regex patterns
FENCE_CODE_RE = re.compile(r"(```[\s\S]*?```|~~~[\s\S]*?~~~)")
DISPLAY_MATH_RE = re.compile(r"(\$\$[\s\S]*?\$\$|\\\[[\s\S]*?\\\])")
INLINE_MATH_RE = re.compile(r"(?<!\\)\$(?!\$)[^$\n]+(?<!\\)\$")
INLINE_CODE_RE = re.compile(r"`[^`\n]+`")
HTML_TAG_RE = re.compile(r"<[^>]+>")
LINK_URL_RE = re.compile(r"(?<!!)\[([^\]]+)\]\(([^)]+)\)")  # [text](url) -> protect url
IMAGE_RE = re.compile(r"!\[[^\]]*\]\([^)]+\)")              # ![alt](url) -> protect entire image
BARE_URL_RE = re.compile(r"https?://[^\s)\]]+")

# Line markers (markdown headers, list bullets, blockquotes)
MARKER_RE = re.compile(r"^(\s*)((?:#{1,6}\s+|>\s+|[-*+]\s+|\d+\.\s+)*)(.*)$")

# Sentinel placeholder pattern (using invisible Unicode characters U+2063 to prevent model mangling)
SENTINEL_TPL = "\u2063PROTECT_{}\u2063"
SENTINEL_RE = re.compile(r"\u2063PROTECT_(\d+)\u2063")

# Split sentences on standard delimiters for models with short context (e.g. NLLB)
SENT_SPLIT_RE = re.compile(r"(?<=[.!?。！？])\s+")


class MarkdownProtector:
    """Extracts sensitive Markdown/LaTeX constructs into a protected registry,

    and restores them after translation.
    """

    def __init__(self):
        self.registry: List[str] = []

    def _stash(self, match: re.Match) -> str:
        idx = len(self.registry)
        self.registry.append(match.group(0))
        return SENTINEL_TPL.format(idx)

    def protect_document(self, content: str) -> str:
        """First pass: protect entire multiline blocks (code blocks, display math, images)."""
        content = FENCE_CODE_RE.sub(self._stash, content)
        content = DISPLAY_MATH_RE.sub(self._stash, content)
        content = IMAGE_RE.sub(self._stash, content)
        return content

    def protect_inline(self, line: str) -> str:
        """Second pass: protect inline items (code, math, URLs, HTML tags)."""
        # Protect links: shield [text](url) structure or url cleanly
        line = LINK_URL_RE.sub(self._stash, line)
        line = INLINE_CODE_RE.sub(self._stash, line)
        line = INLINE_MATH_RE.sub(self._stash, line)
        line = HTML_TAG_RE.sub(self._stash, line)
        line = BARE_URL_RE.sub(self._stash, line)
        return line

    def restore(self, text: str) -> str:
        """Restores all protected tokens in reverse index order."""
        for idx in range(len(self.registry) - 1, -1, -1):
            sentinel = SENTINEL_TPL.format(idx)
            text = text.replace(sentinel, self.registry[idx])
        return text


def parse_and_process_lines(
    content: str,
    translate_fn,
    max_chunk_chars: int = 400
) -> str:
    """Processes Markdown line-by-line, isolating markdown syntax from prose."""
    protector = MarkdownProtector()

    # Pass 1: Shield major block structures
    shielded_content = protector.protect_document(content)

    out_lines = []
    lines = shielded_content.splitlines()

    for line in lines:
        stripped = line.strip()

        # 1. Blank line, pure sentinel line, or table divider line (|---|---|)
        if not stripped:
            out_lines.append(line)
            continue

        if re.match(r"^\|?[\s\-:]+(\|[\s\-:]+)+\|?$", stripped):
            out_lines.append(line)
            continue

        # 2. Table row: process cell by cell so table pipes are preserved
        if stripped.startswith("|") and stripped.endswith("|"):
            cells = line.split("|")
            translated_cells = []
            for idx, cell in enumerate(cells):
                # Edge items before first pipe or after last pipe
                if idx == 0 or idx == len(cells) - 1:
                    translated_cells.append(cell)
                    continue

                cell_strip = cell.strip()
                if not cell_strip:
                    translated_cells.append(cell)
                    continue

                protected_cell = protector.protect_inline(cell)
                # Translate text inside cell
                trans_cell = _translate_segmented_text(protected_cell, translate_fn, max_chunk_chars)
                # Maintain cell whitespace padding
                translated_cells.append(f" {trans_cell.strip()} ")

            out_lines.append("|".join(translated_cells))
            continue

        # 3. Normal prose or header / list / quote line
        m = MARKER_RE.match(line)
        if m:
            indent, markers, body = m.group(1), m.group(2), m.group(3)
            if not body.strip():
                out_lines.append(line)
                continue

            protected_body = protector.protect_inline(body)
            translated_body = _translate_segmented_text(protected_body, translate_fn, max_chunk_chars)
            out_lines.append(indent + markers + translated_body)
        else:
            protected_line = protector.protect_inline(line)
            translated_line = _translate_segmented_text(protected_line, translate_fn, max_chunk_chars)
            out_lines.append(translated_line)

    reconstructed = "\n".join(out_lines)
    return protector.restore(reconstructed)


def _translate_segmented_text(text: str, translate_fn, max_chars: int) -> str:
    """Handles sentence segmentation for short-context translation engines (NLLB)

    while skipping pure sentinels.
    """
    if not text.strip():
        return text

    # If the text is purely a sentinel, do not translate
    if SENTINEL_RE.fullmatch(text.strip()):
        return text

    # Split text into fragments around sentinel tokens
    # e.g., 'Hello ' + '⁣PROTECT_0⁣' + ' world'
    parts = re.split(r"(\u2063PROTECT_\d+\u2063)", text)
    result_parts = []

    for part in parts:
        if not part:
            continue
        if SENTINEL_RE.fullmatch(part):
            result_parts.append(part)
        elif not part.strip():
            result_parts.append(part)
        else:
            # Segment long text into sentences if needed
            if len(part) > max_chars:
                sentences = SENT_SPLIT_RE.split(part)
                trans_sentences = [
                    translate_fn(s) if s.strip() else s for s in sentences
                ]
                result_parts.append(" ".join(trans_sentences))
            else:
                result_parts.append(translate_fn(part))

    return "".join(result_parts)
