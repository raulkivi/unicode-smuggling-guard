"""Recognises files that AI coding agents load as instructions, skills or MCP configuration."""

from pathlib import PurePath

from .files import STDIN

_NAMES = frozenset(name.casefold() for name in [
    'AGENTS.md', 'AGENT.md', 'CLAUDE.md', 'CLAUDE.local.md', 'GEMINI.md', 'SKILL.md',
    '.cursorrules', '.windsurfrules', '.clinerules', 'copilot-instructions.md',
    'mcp.json', '.mcp.json', 'claude_desktop_config.json',
])

# Copilot prompt files and custom instructions/agents, Cursor rules.
_SUFFIXES = ('.instructions.md', '.prompt.md', '.chatmode.md', '.agent.md', '.mdc')

# Everything under these is agent configuration: commands, skills, subagents, rules, hooks, settings.
_DIRS = frozenset(['.claude', '.cursor', '.windsurf', '.clinerules', '.gemini', '.kiro', '.junie', '.amazonq', '.roo'])

_GITHUB_DIRS = frozenset(['instructions', 'prompts', 'agents', 'chatmodes'])


def _in_agent_directory(dirs: list[str]) -> bool:
    if any(d in _DIRS for d in dirs):
        return True
    return any(a == '.github' and b in _GITHUB_DIRS for a, b in zip(dirs, dirs[1:], strict=False))


def is_agent_file(path: str) -> bool:
    """True for agent instruction, skill and MCP config files, and for stdin ('-')."""
    if path == STDIN:
        # Piped input is how MCP tool descriptions and prompts reach the scanner.
        return True
    parts = [part.casefold() for part in PurePath(path).parts]
    name = parts[-1]
    return name in _NAMES or name.endswith(_SUFFIXES) or _in_agent_directory(parts[:-1])
