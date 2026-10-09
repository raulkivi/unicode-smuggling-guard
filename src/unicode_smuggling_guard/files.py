"""Chooses which files to scan and reads them as text."""

import codecs
import os
import subprocess
import sys
from collections.abc import Iterable, Iterator
from dataclasses import dataclass

MAX_BYTES = 10 * 1024 * 1024
STDIN = '-'


def _is_regular_file(path: str) -> bool:
    # Symlinks are skipped so a committed link cannot point the scanner outside the repo.
    return os.path.isfile(path) and not os.path.islink(path)


def _git_files(directory: str) -> list[str] | None:
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
        if path == STDIN:
            yield path
        elif os.path.isdir(path):
            listed = _git_files(path)
            found = listed if listed is not None else _walk(path)
            yield from (os.path.normpath(p) for p in found)
        else:
            yield os.path.normpath(path)


def _read_bytes(path: str, max_bytes: int) -> bytes | None:
    if path == STDIN:
        data = sys.stdin.buffer.read(max_bytes + 1)
        return data if len(data) <= max_bytes else None
    if os.path.getsize(path) > max_bytes:
        return None
    with open(path, 'rb') as fh:
        return fh.read()


@dataclass(frozen=True)
class Skipped:
    """Input that could not be read as text, so its contents went unchecked."""

    reason: str


# UTF-32 first: its little-endian mark begins with UTF-16's.
_BOMS = (
    (codecs.BOM_UTF32_LE, 'utf-32-le'), (codecs.BOM_UTF32_BE, 'utf-32-be'),
    (codecs.BOM_UTF16_LE, 'utf-16-le'), (codecs.BOM_UTF16_BE, 'utf-16-be'),
)


def _wide_encoding(data: bytes) -> tuple[str, int] | None:
    for bom, encoding in _BOMS:
        if data.startswith(bom):
            return encoding, len(bom)
    return None


def read_text(path: str, max_bytes: int = MAX_BYTES) -> str | Skipped:
    """File (or stdin for '-') contents as text, or why it cannot be read as text.

    UTF-8 is the default; UTF-16 and UTF-32 are recognised by their byte order mark.
    Anything else with a NUL byte is treated as binary.
    """
    data = _read_bytes(path, max_bytes)
    if data is None:
        return Skipped(f'larger than {max_bytes:,} bytes')
    wide = _wide_encoding(data)
    if wide is not None:
        encoding, bom_length = wide
        return data[bom_length:].decode(encoding, errors='replace')
    if b'\0' in data:
        return Skipped('contains NUL bytes (binary, or UTF-16/32 without a byte order mark)')
    return data.decode('utf-8', errors='replace')
