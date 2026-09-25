"""Classification of single code points into hidden-character categories."""

import pytest

from unicode_smuggling_guard.categories import Category, classify


@pytest.mark.parametrize('ch', ['a', 'Z', '0', ' ', '\t', '\n', '\r', '\f', '\xe9', '\u0436', '\u4e2d', '\U0001f600', '\u20e3'])
def test_ordinary_characters_are_not_flagged(ch):
    assert classify(ch) is None


@pytest.mark.parametrize('cp', [0xE0000, 0xE0001, 0xE0020, 0xE0041, 0xE007E, 0xE007F])
def test_tags_block(cp):
    assert classify(chr(cp)) is Category.TAG


@pytest.mark.parametrize('cp', [0xFE00, 0xFE0F, 0xE0100, 0xE01EF])
def test_variation_selectors(cp):
    assert classify(chr(cp)) is Category.VARIATION_SELECTOR


@pytest.mark.parametrize('cp', [0x202A, 0x202B, 0x202C, 0x202D, 0x202E, 0x2066, 0x2067, 0x2068, 0x2069, 0x200E, 0x200F, 0x061C])
def test_bidi_controls(cp):
    assert classify(chr(cp)) is Category.BIDI


@pytest.mark.parametrize('cp', [0x200B, 0x200C, 0x200D, 0x2060, 0xFEFF, 0x180E])
def test_zero_width(cp):
    assert classify(chr(cp)) is Category.ZERO_WIDTH


@pytest.mark.parametrize('cp', [0x00, 0x07, 0x0B, 0x1B, 0x7F, 0x80, 0x9F])
def test_control_characters(cp):
    assert classify(chr(cp)) is Category.CONTROL


@pytest.mark.parametrize('cp', [0x00AD, 0x2061, 0x2062, 0x2063, 0x2064, 0x3164, 0x115F, 0x1160, 0xFFA0, 0x034F])
def test_other_invisible_characters(cp):
    assert classify(chr(cp)) is Category.INVISIBLE


def test_category_slugs_are_stable_cli_names():
    assert [c.value for c in Category] == [
        'tag', 'variation-selector', 'bidi', 'zero-width', 'control', 'invisible',
    ]
