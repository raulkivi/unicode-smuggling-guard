"""Hidden-character categories and the code points that belong to each."""

import enum
import unicodedata


class Category(enum.Enum):
    """Kinds of invisible character, ordered by how directly they carry a payload."""

    TAG = 'tag'
    VARIATION_SELECTOR = 'variation-selector'
    BIDI = 'bidi'
    ZERO_WIDTH = 'zero-width'
    CONTROL = 'control'
    INVISIBLE = 'invisible'


TAG_RANGE = (0xE0000, 0xE007F)

# VS1-16 and the VS17-256 supplement. Category Mn, so str.isprintable() is True
# even though they render with zero width; one byte of payload fits in each.
VARIATION_SELECTOR_RANGES = ((0xFE00, 0xFE0F), (0xE0100, 0xE01EF))

# Embeddings, overrides, isolates and marks: reorder how code displays
# without changing what compilers or LLMs read (Trojan Source, CVE-2021-42574).
_BIDI = frozenset(
    list(range(0x202A, 0x202F)) + list(range(0x2066, 0x206A)) + [0x200E, 0x200F, 0x061C]
)

_ZERO_WIDTH = frozenset([0x200B, 0x200C, 0x200D, 0x2060, 0xFEFF, 0x180E])

# Characters that render blank but are not in category Cf, so need listing.
_INVISIBLE_EXTRA = frozenset([0x034F, 0x115F, 0x1160, 0x2028, 0x2029, 0x3164, 0xFFA0])

_ALLOWED_CONTROLS = frozenset('\t\n\r\f')


def _in_range(cp: int, lo_hi) -> bool:
    lo, hi = lo_hi
    return lo <= cp <= hi


def is_variation_selector(ch: str) -> bool:
    cp = ord(ch)
    return any(_in_range(cp, r) for r in VARIATION_SELECTOR_RANGES)


def classify(ch: str) -> Category | None:
    """Return the hidden-character category of *ch*, or None if it is ordinary."""
    cp = ord(ch)
    if _in_range(cp, TAG_RANGE):
        return Category.TAG
    if is_variation_selector(ch):
        return Category.VARIATION_SELECTOR
    if cp in _BIDI:
        return Category.BIDI
    if cp in _ZERO_WIDTH:
        return Category.ZERO_WIDTH
    general = unicodedata.category(ch)
    if general == 'Cc':
        return None if ch in _ALLOWED_CONTROLS else Category.CONTROL
    if general == 'Cf' or cp in _INVISIBLE_EXTRA:
        return Category.INVISIBLE
    return None
