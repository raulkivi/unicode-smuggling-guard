"""Rendering findings for terminals, GitHub annotations and job summaries."""

from unicode_smuggling_guard.categories import Category
from unicode_smuggling_guard.report import describe, format_github, format_text, summary_markdown
from unicode_smuggling_guard.scanner import Finding


def _tag_finding(text, line=3, column=7):
    return Finding(line, column, Category.TAG, tuple(0xE0000 + ord(c) for c in text))


ZWSP = Finding(1, 4, Category.ZERO_WIDTH, (0x200B,))


def test_single_character_is_named():
    assert describe(ZWSP) == 'zero-width: 1 hidden character U+200B ZERO WIDTH SPACE'


def test_run_shows_range_and_decoded_payload():
    assert describe(_tag_finding('Hi')) == 'tag: 2 hidden characters U+E0048..U+E0069 decode to "Hi"'


def test_decoded_payload_escapes_control_characters():
    message = describe(_tag_finding('a\x1b'))
    assert '\x1b' not in message


def test_decoded_newlines_are_escaped():
    vs_newline = Finding(1, 1, Category.VARIATION_SELECTOR, (0xE0100 + ord('a') - 16, 0xFE0A, 0xE0100 + ord('b') - 16))
    assert describe(vs_newline).endswith('decode to "a\\nb"')


def test_long_payload_is_truncated():
    message = describe(_tag_finding('x' * 500))
    assert message.endswith('\u2026"')
    assert len(message) < 250


def test_text_format_is_compiler_style():
    assert format_text('docs/a.md', ZWSP) == 'docs/a.md:1:4: zero-width: 1 hidden character U+200B ZERO WIDTH SPACE'


def test_github_format_is_error_annotation():
    assert format_github('docs/a.md', ZWSP) == (
        '::error file=docs/a.md,line=1,col=4,title=Hidden Unicode (zero-width)::'
        'zero-width: 1 hidden character U+200B ZERO WIDTH SPACE'
    )


def test_github_format_cannot_be_broken_by_payload():
    # A smuggled newline must not start a new workflow command.
    finding = _tag_finding('x\n::set-env name=A::b')
    line = format_github('a.md', finding)
    assert '\n' not in line and '\r' not in line
    assert line.startswith('::error ')


def test_github_format_escapes_percent_in_message():
    assert '%25' in format_github('a.md', _tag_finding('100%'))


def test_github_format_escapes_property_separators_in_path():
    assert format_github('a,b:c%.md', ZWSP).startswith('::error file=a%2Cb%3Ac%25.md,')


def test_summary_lists_each_finding_in_a_table():
    summary = summary_markdown([('a.md', ZWSP), ('b.md', _tag_finding('Hi'))])
    assert summary.startswith('### Hidden Unicode found\n')
    assert '| a.md | 1:4 | zero-width |' in summary
    assert '| b.md | 3:7 | tag |' in summary


def test_summary_neutralises_markdown_in_payload():
    summary = summary_markdown([('a.md', _tag_finding('![x](https://evil.test/p.png)|'))])
    assert '![x](' not in summary
    assert '\\|' in summary


def test_empty_summary_reports_clean_scan():
    assert summary_markdown([]) == '### Hidden Unicode: none found\n'


IM_START = Finding(2, 5, Category.CONTROL_TOKEN, tuple(map(ord, '<|im_start|>')))


def test_control_token_is_quoted():
    assert describe(IM_START) == 'control-token: chat-template token "<|im_start|>"'


def test_control_token_annotation_has_its_own_title():
    assert format_github('SKILL.md', IM_START).startswith(
        '::error file=SKILL.md,line=2,col=5,title=Chat-template token (control-token)::'
    )


def test_control_token_is_escaped_in_summary():
    assert '\\<\\|im\\_start\\|\\>' in summary_markdown([('SKILL.md', IM_START)])
