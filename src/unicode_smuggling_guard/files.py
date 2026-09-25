"""Chooses which files to scan and reads them as text."""

import os
import subprocess
from typing import Iterable, Iterator, List, Optional

MAX_BYTES = 10 * 1024 * 1024


def _is_regular_file(path: str) -> bool:
    # Symlinks are skipped so a committed link cannot point the scanner outside the repo.
    return os.path.isfile(path) and not os.path.islink(path)


def _git_files(directory: str) -> Optional[List[str]]:
    """Tracked and untracked-but-not-ignored files, or None outside a git work tree."""
    try:
        listing = subprocess.run(
            ['git', '-C', directory, 'ls-files', '-z', '--cached', '--others', '--exclude-standard'],
            capture_output=True, check=True,
        ).stdout
    except (OSError, subprocess.CalledProcessError):
        return None
    names = (n for n in listing.decode('utf-8', 'surrogateescape').split('\0') if n)
    return [p for p in (os.path.join(directory, n) for n in names) if _is_regular_file(p)]


def _walk(directory: str) -> Iterator[str]:
    for root, dirs, files in os.walk(directory):
        dirs[:] = sorted(d for d in dirs if d != '.git')
        for name in sorted(files):
            path = os.path.join(root, name)
            if _is_regular_file(path):
                yield path


def iter_files(paths: Iterable[str]) -> Iterator[str]:
    """Expand directories (honouring .gitignore when inside git) into file paths."""
    for path in paths:
        if os.path.isdir(path):
            listed = _git_files(path)
            found = listed if listed is not None else _walk(path)
            yield from (os.path.normpath(p) for p in found)
        else:
            yield os.path.normpath(path)


def read_text(path: str, max_bytes: int = MAX_BYTES) -> Optional[str]:
    """File contents as text, or None for binary or oversized files."""
    if os.path.getsize(path) > max_bytes:
        return None
    with open(path, 'rb') as fh:
        data = fh.read()
    if b'\0' in data:
        return None
    return data.decode('utf-8', errors='replace')
