"""Finds runs of hidden characters in text, skipping their legitimate uses."""

import re
import unicodedata
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


# The only recommended (RGI) emoji tag sequences: the England, Scotland and Wales
# flags, BLACK FLAG + region tags + CANCEL TAG. Any other tag run, even one shaped
# like a subdivision code, renders as a plain black flag and carries hidden text.
_RGI_FLAG_REGIONS = ('gbeng', 'gbsct', 'gbwls')
_FLAG_TAG_SEQUENCE = re.compile(
    '\U0001F3F4((?:'
    + '|'.join(''.join(chr(0xE0000 + ord(c)) for c in region) for region in _RGI_FLAG_REGIONS)
    + ')\U000E007F)'
)

# Only these can appear in pure-ASCII text; lets clean ASCII files skip the per-character walk.
_ASCII_SUSPICIOUS = frozenset(ch for ch in map(chr, range(0x80)) if classify(ch) is not None)

_JOINERS = frozenset('\u200c\u200d')
_BOM = '\ufeff'

# VS15/VS16 choose text or emoji presentation; every other selector in
# U+FE00-FE0D has no use in prose, code or emoji.
_PRESENTATION_SELECTORS = frozenset('\ufe0e\ufe0f')
# The only ASCII characters with standardised variation sequences (keycap emoji).
_KEYCAP_BASES = frozenset('#*0123456789')
# Code points that can take an emoji presentation selector: the bases in
# emoji-variation-sequences.txt, widened to their blocks so new emoji need no update.
_PICTOGRAPHIC_RANGES = (
    (0x00A9, 0x00A9), (0x00AE, 0x00AE), (0x203C, 0x203C), (0x2049, 0x2049),
    (0x2122, 0x2122), (0x2139, 0x2139), (0x2194, 0x21AA), (0x231A, 0x23FF),
    (0x24C2, 0x24C2), (0x25AA, 0x25FE), (0x2600, 0x27BF), (0x2934, 0x2935),
    (0x2B05, 0x2B55), (0x3030, 0x3030), (0x303D, 0x303D), (0x3297, 0x3297),
    (0x3299, 0x3299), (0x1F000, 0x1FAFF),
)
_IDEOGRAPHIC_SELECTORS = (0xE0100, 0xE01EF)


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


def _is_pictographic(ch: str) -> bool:
    cp = ord(ch)
    return any(lo <= cp <= hi for lo, hi in _PICTOGRAPHIC_RANGES)


def _is_cjk_ideograph(ch: str) -> bool:
    return unicodedata.name(ch, '').startswith('CJK UNIFIED IDEOGRAPH-')


def _selector_fits_base(selector: str, base: str) -> bool:
    """VS15/VS16 after an emoji or keycap base; VS17-256 after a CJK ideograph."""
    if selector in _PRESENTATION_SELECTORS:
        return base in _KEYCAP_BASES or _is_pictographic(base)
    lo, hi = _IDEOGRAPHIC_SELECTORS
    return lo <= ord(selector) <= hi and _is_cjk_ideograph(base)


def _selects_single_variant(text: str, i: int) -> bool:
    """One selector of the kind its base takes picks a glyph variant; any other carries a byte."""
    if i == 0 or not _selector_fits_base(text[i], text[i - 1]):
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
    if text.isascii() and _ASCII_SUSPICIOUS.isdisjoint(text):
        return []
    return list(_runs(text))
