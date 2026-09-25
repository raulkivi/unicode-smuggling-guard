"""Renders findings as terminal lines, GitHub annotations and job summaries.

Decoded payloads are attacker-controlled, so every output escapes them for
its medium: control characters for terminals, workflow-command separators for
GitHub, and Markdown syntax for job summaries.
"""

import re
import unicodedata
from collections.abc import Sequence

from .decode import decode
from .scanner import Finding

_PAYLOAD_PREVIEW = 120


def _codepoint(cp: int) -> str:
    return f'U+{cp:04X}'


def _printable(text: str) -> str:
    escaped = ''.join(
        c if c.isprintable() else c.encode('unicode_escape').decode('ascii') for c in text
    )
    return escaped if len(escaped) <= _PAYLOAD_PREVIEW else escaped[:_PAYLOAD_PREVIEW] + '\u2026'


def describe(finding: Finding) -> str:
    """One-line explanation: category, what was found, and any decoded payload."""
    cps = finding.codepoints
    if len(cps) == 1:
        name = unicodedata.name(chr(cps[0]), '')
        found = f'1 hidden character {_codepoint(cps[0])}' + (f' {name}' if name else '')
    else:
        found = f'{len(cps)} hidden characters {_codepoint(cps[0])}..{_codepoint(cps[-1])}'
    payload = decode(finding.category, cps)
    decoded = f' decode to "{_printable(payload)}"' if payload else ''
    return f'{finding.category.value}: {found}{decoded}'


def format_text(path: str, finding: Finding) -> str:
    return f'{path}:{finding.line}:{finding.column}: {describe(finding)}'


def _escape_command_data(text: str) -> str:
    return text.replace('%', '%25').replace('\r', '%0D').replace('\n', '%0A')


def _escape_command_property(text: str) -> str:
    return _escape_command_data(text).replace(':', '%3A').replace(',', '%2C')


def format_github(path: str, finding: Finding) -> str:
    """A workflow ::error command, so the finding shows inline on the PR diff."""
    props = ','.join([
        f'file={_escape_command_property(path)}',
        f'line={finding.line}',
        f'col={finding.column}',
        f'title={_escape_command_property(f"Hidden Unicode ({finding.category.value})")}',
    ])
    return f'::error {props}::{_escape_command_data(describe(finding))}'


_MARKDOWN_SYNTAX = re.compile(r'([\\`*_\[\]()!<>|~#&])')


def _escape_markdown(text: str) -> str:
    return _MARKDOWN_SYNTAX.sub(r'\\\1', text)


def summary_markdown(results: Sequence[tuple[str, Finding]]) -> str:
    """Markdown table for $GITHUB_STEP_SUMMARY."""
    if not results:
        return '### Hidden Unicode: none found\n'
    rows = [
        f'| {_escape_markdown(path)} | {f.line}:{f.column} | {f.category.value} | {_escape_markdown(describe(f))} |'
        for path, f in results
    ]
    header = ['### Hidden Unicode found', '', '| File | Line:Col | Category | Detail |', '|---|---|---|---|']
    return '\n'.join(header + rows) + '\n'
