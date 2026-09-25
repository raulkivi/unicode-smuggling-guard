"""Recovers the text an attacker encoded into a run of hidden characters."""

from collections.abc import Sequence

from .categories import Category

_TAG_BASE = 0xE0000
_TAG_PRINTABLE = (0xE0020, 0xE007E)


def _decode_tags(codepoints: Sequence[int]) -> str:
    lo, hi = _TAG_PRINTABLE
    return ''.join(chr(cp - _TAG_BASE) for cp in codepoints if lo <= cp <= hi)


def _variation_selector_byte(cp: int) -> int:
    # VS1-16 carry bytes 0-15, VS17-256 carry bytes 16-255.
    return cp - 0xFE00 if cp <= 0xFE0F else cp - 0xE0100 + 16


def _decode_variation_selectors(codepoints: Sequence[int]) -> str | None:
    try:
        return bytes(_variation_selector_byte(cp) for cp in codepoints).decode('utf-8')
    except UnicodeDecodeError:
        return None


_DECODERS = {
    Category.TAG: _decode_tags,
    Category.VARIATION_SELECTOR: _decode_variation_selectors,
}


def _has_readable_text(text: str) -> bool:
    return any(c.isprintable() and not c.isspace() for c in text)


def decode(category: Category, codepoints: Sequence[int]) -> str | None:
    """Return the hidden text, or None if the run encodes nothing readable."""
    decoder = _DECODERS.get(category)
    if decoder is None:
        return None
    text = decoder(codepoints)
    return text if text and _has_readable_text(text) else None
