"""Recognising files whose text AI coding agents load as instructions or tool metadata."""

import os

import pytest

from unicode_smuggling_guard.agent_files import is_agent_file


def _path(*parts):
    return os.path.join(*parts)


@pytest.mark.parametrize('path', [
    _path('AGENTS.md'),
    _path('services', 'api', 'AGENTS.md'),
    _path('CLAUDE.md'),
    _path('CLAUDE.local.md'),
    _path('GEMINI.md'),
    _path('skills', 'deploy', 'SKILL.md'),
    _path('agents.md'),
    _path('.cursorrules'),
    _path('.windsurfrules'),
    _path('.github', 'copilot-instructions.md'),
    _path('.mcp.json'),
    _path('.vscode', 'mcp.json'),
    _path('claude_desktop_config.json'),
])
def test_agent_file_names(path):
    assert is_agent_file(path)


@pytest.mark.parametrize('path', [
    _path('docs', 'review.prompt.md'),
    _path('api.instructions.md'),
    _path('planner.chatmode.md'),
    _path('reviewer.agent.md'),
    _path('rules', 'style.mdc'),
])
def test_agent_file_suffixes(path):
    assert is_agent_file(path)


@pytest.mark.parametrize('path', [
    _path('.claude', 'commands', 'deploy.md'),
    _path('.claude', 'settings.json'),
    _path('.cursor', 'rules', 'python.md'),
    _path('.windsurf', 'rules', 'a.md'),
    _path('.clinerules', 'style.md'),
    _path('.gemini', 'settings.json'),
    _path('.kiro', 'steering', 'product.md'),
    _path('.github', 'instructions', 'tests.md'),
    _path('.github', 'prompts', 'release.md'),
    _path('.github', 'agents', 'reviewer.md'),
    _path('repo', '.claude', 'agents', 'planner.md'),
])
def test_files_in_agent_directories(path):
    assert is_agent_file(path)


@pytest.mark.parametrize('path', [
    _path('README.md'),
    _path('src', 'app.py'),
    _path('docs', 'agents', 'guide.md'),
    _path('.github', 'workflows', 'ci.yml'),
    _path('.github', 'CODEOWNERS'),
    _path('package.json'),
    _path('claude.py'),
])
def test_other_files_are_not_agent_files(path):
    assert not is_agent_file(path)


def test_standard_input_counts_as_agent_content():
    # Piped input is how MCP tool descriptions and prompts reach the scanner.
    assert is_agent_file('-')
