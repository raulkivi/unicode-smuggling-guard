"""Coverage-guided fuzzing of the scanner and every report format with Atheris.

    python fuzz/fuzz_scan.py -max_total_time=300

Checks the same safety invariants as tests/test_properties.py, but lets
libFuzzer's coverage feedback steer inputs into rarely taken branches.
"""

import sys

import atheris

with atheris.instrument_imports():
    from unicode_smuggling_guard.report import format_github, format_text, summary_markdown
    from unicode_smuggling_guard.scanner import scan


def test_one_input(data: bytes) -> None:
    text = atheris.FuzzedDataProvider(data).ConsumeUnicodeNoSurrogates(len(data))
    results = [('fuzz.md', finding) for finding in scan(text)]
    for path, finding in results:
        annotation = format_github(path, finding)
        if '\n' in annotation or '\r' in annotation:
            raise AssertionError(f'annotation spans lines: {annotation!r}')
        line = format_text(path, finding)
        if not line.isprintable():
            raise AssertionError(f'terminal output has control characters: {line!r}')
    summary_markdown(results)


def main() -> None:
    atheris.Setup(sys.argv, test_one_input)
    atheris.Fuzz()


if __name__ == '__main__':
    main()
