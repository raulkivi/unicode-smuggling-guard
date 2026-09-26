"""Finding chat-template control tokens that forge conversation turns."""

import pytest

from unicode_smuggling_guard.categories import Category
from unicode_smuggling_guard.tokens import scan_control_tokens


def _tokens(text):
    return [''.join(map(chr, f.codepoints)) for f in scan_control_tokens(text)]


@pytest.mark.parametrize('token', [
    '<|im_start|>',  # ChatML: Qwen, many fine-tunes
    '<|im_end|>',
    '<|endoftext|>',
    '<|start_header_id|>',  # Llama 3
    '<|eot_id|>',
    '<|assistant|>',  # Phi-3, GLM
    '<|channel|>',  # gpt-oss harmony
    '<start_of_turn>',  # Gemma
    '<end_of_turn>',
    '[INST]',  # Mistral, Llama 2
    '[/INST]',
    '[SYSTEM_PROMPT]',
    '[TOOL_CALLS]',
    '<<SYS>>',  # Llama 2
    '<</SYS>>',
    '<\uff5cUser\uff5c>',  # DeepSeek: fullwidth vertical bars
    '<\uff5cbegin\u2581of\u2581sentence\uff5c>',
])
def test_known_tokens_are_found(token):
    assert _tokens(f'Summarise the file. {token}system\n') == [token]


@pytest.mark.parametrize('text', [
    '<div>',
    'a || b',
    '<|',
    'x <| y |> z',
    '[link](https://example.com)',
    '[INSTALL]',
    '<start_of_turnaround>',
    '<< SYS >>',
])
def test_ordinary_text_has_no_tokens(text):
    assert _tokens(text) == []


def test_findings_carry_category_and_position():
    [first, second] = scan_control_tokens('ok\nab<|im_end|><|im_start|>system\n')
    assert (first.line, first.column, first.category) == (2, 3, Category.CONTROL_TOKEN)
    assert (second.line, second.column) == (2, 13)


def test_column_counts_code_points_not_bytes():
    [finding] = scan_control_tokens('p\xe4\xe4 [INST]')
    assert finding.column == 5
