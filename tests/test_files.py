"""Finding the text files to scan and reading them safely."""

import os
import shutil
import subprocess

import pytest

from unicode_smuggling_guard.files import iter_files, read_text


def _write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return path


def test_explicit_file_is_yielded(tmp_path):
    f = _write(tmp_path / 'a.md', b'x')
    assert list(iter_files([str(f)])) == [str(f)]


def test_directory_without_git_is_walked_skipping_dot_git(tmp_path):
    _write(tmp_path / 'a.md', b'x')
    _write(tmp_path / 'sub' / 'b.py', b'x')
    _write(tmp_path / '.git' / 'config', b'x')
    found = sorted(os.path.relpath(p, tmp_path) for p in iter_files([str(tmp_path)]))
    assert found == ['a.md', os.path.join('sub', 'b.py')]


@pytest.mark.skipif(shutil.which('git') is None, reason='git not installed')
def test_git_directory_respects_gitignore(tmp_path):
    subprocess.run(['git', 'init', '-q', str(tmp_path)], check=True)
    _write(tmp_path / '.gitignore', b'node_modules/\n')
    _write(tmp_path / 'node_modules' / 'dep.js', b'x')
    _write(tmp_path / 'SKILL.md', b'x')
    found = sorted(os.path.relpath(p, tmp_path) for p in iter_files([str(tmp_path)]))
    assert found == ['.gitignore', 'SKILL.md']


def test_utf8_text_is_read(tmp_path):
    f = _write(tmp_path / 'a.md', 'p\xe4ev \u200b'.encode())
    assert read_text(str(f)) == 'p\xe4ev \u200b'


def test_binary_file_is_skipped(tmp_path):
    f = _write(tmp_path / 'a.png', b'\x89PNG\r\n\x1a\n\x00\x00')
    assert read_text(str(f)) is None


def test_binary_with_late_nul_byte_is_skipped(tmp_path):
    # PDFs often have a long text header before the first NUL byte.
    f = _write(tmp_path / 'a.pdf', b'%PDF-1.4\n' + b'a' * 20000 + b'\x00')
    assert read_text(str(f)) is None


def test_invalid_utf8_is_read_with_replacement(tmp_path):
    f = _write(tmp_path / 'a.txt', b'ok \xff \xe2\x80\x8b')
    assert read_text(str(f)) == 'ok \ufffd \u200b'


def test_oversized_file_is_skipped(tmp_path):
    f = _write(tmp_path / 'big.txt', b'a' * 11)
    assert read_text(str(f), max_bytes=10) is None
