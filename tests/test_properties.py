"""Property-based (fuzz) tests: invariants that must hold for any input."""

import string

from hypothesis import assume, given
from hypothesis import strategies as st

from unicode_smuggling_guard.categories import Category, classify
from unicode_smuggling_guard.decode import decode
from unicode_smuggling_guard.report import describe, format_github, format_text, summary_markdown
from unicode_smuggling_guard.scanner import scan
from unicode_smuggling_guard.tokens import scan_control_tokens

ASCII_PREFIX = st.text(alphabet=string.ascii_letters + string.digits + ' .,', max_size=40)
# Tag characters mirror ASCII only, so tag payloads are drawn from U+0000-007F.
ASCII_TEXT = st.text(alphabet=st.characters(max_codepoint=0x7F))


def _tags(text):
    return ''.join(chr(0xE0000 + ord(c)) for c in text)


def _variation_selectors(data):
    return ''.join(chr(0xFE00 + b) if b < 16 else chr(0xE0100 + b - 16) for b in data)


def _char_at(text, line, column):
    return text.split('\n')[line - 1][column - 1]


@given(st.characters())
def test_classify_accepts_every_code_point(ch):
    assert classify(ch) is None or isinstance(classify(ch), Category)


@given(st.text())
def test_findings_point_at_the_characters_they_report(text):
    for finding in scan(text):
        for offset, cp in enumerate(finding.codepoints):
            assert ord(_char_at(text, finding.line, finding.column + offset)) == cp
            assert classify(chr(cp)) is finding.category


@given(st.text())
def test_text_without_hidden_characters_is_clean(text):
    assume(all(classify(c) is None for c in text))
    assert scan(text) == []


@given(ASCII_PREFIX, st.text(alphabet=string.ascii_letters + string.digits + string.punctuation + ' ', min_size=1))
def test_tag_smuggled_ascii_is_found_and_decoded(prefix, payload):
    assume(payload.strip())
    [finding] = scan(prefix + _tags(payload))
    assert finding.category is Category.TAG
    assert decode(finding.category, finding.codepoints) == payload


@given(ASCII_PREFIX, st.text(min_size=2))
def test_variation_selector_smuggled_text_is_found_and_decoded(prefix, payload):
    assume(any(c.isprintable() and not c.isspace() for c in payload))
    [finding] = scan(prefix + '\U0001F600' + _variation_selectors(payload.encode('utf-8')))
    assert finding.category is Category.VARIATION_SELECTOR
    assert decode(finding.category, finding.codepoints) == payload


@given(st.text(), ASCII_TEXT)
def test_github_annotation_is_always_a_single_command(path, payload):
    for finding in scan('x' + _tags(payload) + '\u202e' + _variation_selectors(payload.encode('utf-8'))):
        line = format_github(path, finding)
        assert '\n' not in line and '\r' not in line
        assert line.startswith('::error file=')


@given(ASCII_TEXT)
def test_terminal_output_has_no_control_characters_from_payload(payload):
    for finding in scan('x' + _tags(payload)):
        assert all(c.isprintable() for c in format_text('a.md', finding))


@given(ASCII_TEXT)
def test_summary_row_count_matches_findings(payload):
    findings = [('a.md', f) for f in scan('x' + _tags(payload) + '\u200b')]
    table_rows = [r for r in summary_markdown(findings).split('\n') if r.startswith('| a.md |')]
    assert len(table_rows) == len(findings)


@given(st.text())
def test_describe_never_raises(text):
    for finding in scan(text):
        assert describe(finding).startswith(finding.category.value + ':')


@given(st.text())
def test_control_tokens_point_at_the_text_they_report(text):
    for finding in scan_control_tokens(text):
        token = ''.join(map(chr, finding.codepoints))
        line = text.split('\n')[finding.line - 1]
        assert line[finding.column - 1:finding.column - 1 + len(token)] == token


@given(st.text(), st.text())
def test_control_token_output_is_single_line_and_printable(prefix, name):
    for finding in scan_control_tokens(prefix + '<\uff5c' + name + '\uff5c>'):
        assert all(c.isprintable() for c in format_text('a.md', finding))
        assert '\n' not in format_github('a.md', finding)
