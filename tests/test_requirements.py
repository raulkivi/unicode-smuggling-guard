"""The development lockfile must include pytest's Windows-only dependency."""

import re
from pathlib import Path

from packaging.requirements import Requirement

ROOT = Path(__file__).resolve().parent.parent


def test_windows_colorama_is_pinned_and_hashed():
    lockfile = (ROOT / 'requirements-dev.txt').read_text(encoding='utf-8')
    entries = lockfile.replace('\\\n', '').splitlines()
    colorama = next((line for line in entries if line.startswith('colorama==')), None)
    assert colorama is not None, 'pytest requires colorama on Windows'

    requirement_text, *hashes = colorama.split('--hash=')
    requirement = Requirement(requirement_text.strip())
    assert requirement.marker is None or requirement.marker.evaluate({'sys_platform': 'win32'})
    assert len(requirement.specifier) == 1
    assert next(iter(requirement.specifier)).operator == '=='
    assert hashes
    assert all(re.fullmatch(r'sha256:[0-9a-f]{64}', value.strip()) for value in hashes)
