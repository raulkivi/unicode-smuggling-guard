"""Finds chat-template control tokens: visible text that forges conversation turns.

Serving stacks that render a chat template without escaping content let a file,
web page or tool description containing these tokens open a new system turn.
"""

import re

from .categories import Category
from .scanner import Finding

_CONTROL_TOKEN = re.compile('|'.join([
    r'<\|[A-Za-z0-9_]{1,40}\|>',  # ChatML, Llama 3, Phi, GLM, gpt-oss harmony
    r'<\uff5c[^\uff5c\s]{1,40}\uff5c>',  # DeepSeek, with fullwidth vertical bars
    r'<(?:start|end)_of_turn>',  # Gemma
    r'\[/?(?:INST|SYSTEM_PROMPT|AVAILABLE_TOOLS|TOOL_CALLS|TOOL_RESULTS)\]',  # Mistral, Llama 2
    r'<</?SYS>>',  # Llama 2
]))


def scan_control_tokens(text: str) -> list[Finding]:
    """Return every chat-template control token in *text*, in order."""
    findings = []
    line, line_start, pos = 1, 0, 0
    for match in _CONTROL_TOKEN.finditer(text):
        start = match.start()
        newlines = text.count('\n', pos, start)
        if newlines:
            line += newlines
            line_start = text.rfind('\n', pos, start) + 1
        pos = start
        codepoints = tuple(map(ord, match.group()))
        findings.append(Finding(line, start - line_start + 1, Category.CONTROL_TOKEN, codepoints))
    return findings
