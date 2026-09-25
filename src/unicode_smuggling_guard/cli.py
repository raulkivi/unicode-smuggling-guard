"""Command line: scan files, print findings, exit non-zero if any are found."""

import argparse
import os
import sys
from typing import List, Optional, Sequence, Tuple

from . import __version__
from .categories import Category
from .files import iter_files, read_text
from .report import format_github, format_text, summary_markdown
from .scanner import Finding, scan

PROG = 'unicode-smuggling-guard'

EXIT_CLEAN, EXIT_FOUND, EXIT_USAGE = 0, 1, 2

_FORMATTERS = {'text': format_text, 'github': format_github}


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=PROG,
        description='Detect invisible Unicode used to smuggle instructions into code, docs and AI agent files.',
    )
    parser.add_argument('paths', nargs='*', default=['.'], help='files or directories (default: .)')
    parser.add_argument('--format', choices=sorted(_FORMATTERS), default='text', help='output format')
    parser.add_argument(
        '--ignore', action='append', default=[], metavar='CATEGORY',
        choices=[c.value for c in Category],
        help='category to skip; repeatable. One of: %(choices)s',
    )
    parser.add_argument('--summary', metavar='FILE', help='append a Markdown report (e.g. $GITHUB_STEP_SUMMARY)')
    parser.add_argument('--version', action='version', version=f'%(prog)s {__version__}')
    return parser


def _plural(n: int, word: str) -> str:
    return f'{n} {word}' + ('' if n == 1 else 's')


def _tally(results: Sequence[Tuple[str, Finding]], scanned: int) -> str:
    if not results:
        return f'{PROG}: no hidden Unicode in {_plural(scanned, "file")}'
    dirty = len({path for path, _ in results})
    return f'{PROG}: {_plural(len(results), "hidden run")} in {dirty} of {_plural(scanned, "file")}'


def main(argv: Optional[List[str]] = None) -> int:
    args = _parser().parse_args(argv)
    missing = [p for p in args.paths if not os.path.exists(p)]
    if missing:
        print(f'{PROG}: no such file or directory: {", ".join(missing)}', file=sys.stderr)
        return EXIT_USAGE

    ignored = {Category(value) for value in args.ignore}
    formatter = _FORMATTERS[args.format]
    results: List[Tuple[str, Finding]] = []
    scanned = 0
    for path in iter_files(args.paths):
        text = read_text(path)
        if text is None:
            continue
        scanned += 1
        for finding in scan(text):
            if finding.category in ignored:
                continue
            results.append((path, finding))
            print(formatter(path, finding))

    if args.summary:
        with open(args.summary, 'a', encoding='utf-8') as fh:
            fh.write(summary_markdown(results))
    print(_tally(results, scanned), file=sys.stderr)
    return EXIT_FOUND if results else EXIT_CLEAN
