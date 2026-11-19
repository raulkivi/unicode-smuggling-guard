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
_ZWJ = '\u200d'
_BOM = '\ufeff'

# Scripts where ZWJ/ZWNJ control cursive joining or conjunct and ligature
# formation (Unicode Standard ch. 23.2 "Layout Controls"), as their block ranges
# because the standard library has no Script property. In every other script a
# joiner changes nothing visible, so it can only split keywords or carry bits.
_JOINING_SCRIPTS = {
    'Arabic': ((0x0600, 0x06FF), (0x0750, 0x077F), (0x0870, 0x08FF),
               (0xFB50, 0xFDFF), (0xFE70, 0xFEFF), (0x10EC0, 0x10EFF)),
    'Syriac': ((0x0700, 0x074F), (0x0860, 0x086F)),
    'Thaana': ((0x0780, 0x07BF),),
    'NKo': ((0x07C0, 0x07FF),),
    'Devanagari': ((0x0900, 0x097F), (0xA8E0, 0xA8FF)),
    'Bengali': ((0x0980, 0x09FF),),
    'Gurmukhi': ((0x0A00, 0x0A7F),),
    'Gujarati': ((0x0A80, 0x0AFF),),
    'Oriya': ((0x0B00, 0x0B7F),),
    'Tamil': ((0x0B80, 0x0BFF),),
    'Telugu': ((0x0C00, 0x0C7F),),
    'Kannada': ((0x0C80, 0x0CFF),),
    'Malayalam': ((0x0D00, 0x0D7F),),
    'Sinhala': ((0x0D80, 0x0DFF),),
    'Tibetan': ((0x0F00, 0x0FFF),),
    'Myanmar': ((0x1000, 0x109F), (0xA9E0, 0xA9FF), (0xAA60, 0xAA7F)),
    'Khmer': ((0x1780, 0x17FF),),
    'Mongolian': ((0x1800, 0x18AF), (0x11660, 0x1167F)),
}
# What may follow an emoji before its ZWJ: VS16 and the combining enclosing keycap.
_EMOJI_ELEMENT_SUFFIXES = frozenset('\ufe0f\u20e3')

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


def _joining_script(ch: str) -> str | None:
    if classify(ch) is not None:
        return None
    cp = ord(ch)
    for script, ranges in _JOINING_SCRIPTS.items():
        if any(lo <= cp <= hi for lo, hi in ranges):
            return script
    return None


def _joins_script_letters(text: str, i: int) -> bool:
    """ZWJ/ZWNJ between two characters of one cursive or conjunct-forming script."""
    script = _joining_script(text[i - 1])
    return script is not None and script == _joining_script(text[i + 1])


def _ends_emoji_element(text: str, end: int) -> bool:
    """An emoji, optionally followed by VS16 and/or a keycap mark, ends at *end*."""
    base = end
    while base > max(end - 2, 0) and text[base] in _EMOJI_ELEMENT_SUFFIXES:
        base -= 1
    return _is_pictographic(text[base])


def _joins_emoji(text: str, i: int) -> bool:
    """ZWJ between two elements of an emoji ZWJ sequence (family, couple, flags)."""
    return text[i] == _ZWJ and _ends_emoji_element(text, i - 1) and _is_pictographic(text[i + 1])


def _joiner_shapes_rendering(text: str, i: int) -> bool:
    if i == 0 or i + 1 >= len(text):
        return False
    return _joins_emoji(text, i) or _joins_script_letters(text, i)


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
        if ch in _JOINERS and _joiner_shapes_rendering(text, i):
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
