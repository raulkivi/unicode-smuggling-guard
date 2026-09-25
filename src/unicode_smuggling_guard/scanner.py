"""Finds runs of hidden characters in text, skipping their legitimate uses."""

import re
from collections.abc import Iterator
from dataclasses import dataclass

from .categories import Category, classify, is_variation_selector


@dataclass(frozen=True)
class Finding:
    """A run of same-category hidden characters starting at line:column (1-based)."""

    line: int
    column: int
    category: Category
    codepoints: tuple[int, ...]


# Subdivision flags (England, Scotland, Wales): BLACK FLAG + 1-6 lowercase or
# digit tags + CANCEL TAG. Any other tag sequence has no rendering purpose.
_FLAG_TAG_SEQUENCE = re.compile('\U0001F3F4([\U000E0030-\U000E0039\U000E0061-\U000E007A]{1,6}\U000E007F)')

# Only these can appear in pure-ASCII text; lets clean ASCII files skip the per-character walk.
_ASCII_SUSPICIOUS = re.compile('[\x00-\x08\x0b\x0e-\x1f\x7f]')

_JOINERS = frozenset('\u200c\u200d')
# The only ASCII characters with standardised variation sequences (keycap emoji).
_KEYCAP_BASES = frozenset('#*0123456789')
_BOM = '\ufeff'


def _flag_tag_indices(text: str) -> frozenset[int]:
    return frozenset(
        i for m in _FLAG_TAG_SEQUENCE.finditer(text) for i in range(m.start(1), m.end(1))
    )


def _is_visible_base(ch: str) -> bool:
    return classify(ch) is None and not ch.isspace()


def _joins_non_ascii(text: str, i: int) -> bool:
    """ZWJ/ZWNJ inside emoji sequences and Arabic/Indic words shape rendering."""
    if i == 0 or i + 1 >= len(text):
        return False
    before, after = text[i - 1], text[i + 1]
    before_ok = is_variation_selector(before) or (_is_visible_base(before) and not before.isascii())
    return before_ok and _is_visible_base(after) and not after.isascii()


def _selects_single_variant(text: str, i: int) -> bool:
    """One selector after an emoji, CJK or keycap base picks a glyph variant."""
    if i == 0:
        return False
    base = text[i - 1]
    if not _is_visible_base(base) or (base.isascii() and base not in _KEYCAP_BASES):
        return False
    return i + 1 >= len(text) or not is_variation_selector(text[i + 1])


def _suspicious(text: str, i: int, allowed_tags: frozenset[int]) -> Category | None:
    ch = text[i]
    category = classify(ch)
    if category is Category.TAG and i in allowed_tags:
        return None
    if category is Category.VARIATION_SELECTOR and _selects_single_variant(text, i):
        return None
    if category is Category.ZERO_WIDTH:
        if ch == _BOM and i == 0:
            return None
        if ch in _JOINERS and _joins_non_ascii(text, i):
            return None
    return category


def _runs(text: str) -> Iterator[Finding]:
    allowed_tags = _flag_tag_indices(text)
    line, column = 1, 0
    start: tuple[int, int, Category] | None = None
    codepoints: list[int] = []
    for i, ch in enumerate(text):
        column += 1
        category = _suspicious(text, i, allowed_tags)
        if start is not None and category is start[2]:
            codepoints.append(ord(ch))
        else:
            if start is not None:
                yield Finding(*start, tuple(codepoints))
            start = (line, column, category) if category else None
            codepoints = [ord(ch)]
        if ch == '\n':
            line, column = line + 1, 0
    if start is not None:
        yield Finding(*start, tuple(codepoints))


def scan(text: str) -> list[Finding]:
    """Return every run of hidden characters in *text*, in order."""
    if text.isascii() and not _ASCII_SUSPICIOUS.search(text):
        return []
    return list(_runs(text))
