# Contributing

## Reporting

- Bugs, false positives, missed characters and feature requests: [open an issue](https://github.com/raulkivi/unicode-smuggling-guard/issues). Include the input as `\uXXXX` escapes, not literal characters; invisible characters get lost or altered in copy-paste.
- Security vulnerabilities: do not open an issue. Follow [SECURITY.md](SECURITY.md).

Issues and pull requests are answered within 7 days.

## Changing code

1. Fork the repository and create a branch from `main`.
2. Write the test first. Every change in behaviour needs a test that fails before the change and passes after it. New detection rules also need a case in `tests/test_properties.py` if they affect an invariant there.
3. Make the change.
4. Run the checks:
   ```sh
   python -m pip install --require-hashes -r requirements-dev.txt
   python -m ruff check .
   python -m pytest
   python -m unicode_smuggling_guard .   # with PYTHONPATH=src; the repo must scan clean
   ```
5. For user-visible changes, add a line under `[Unreleased]` in [CHANGELOG.md](CHANGELOG.md).
6. Open a pull request against `main`. Merging needs passing CI (tests on Linux, macOS and Windows, lint, and the Action self-test).

## Requirements for contributions

- **No runtime dependencies.** The package must stay installable and runnable with the standard library only.
- **Python 3.10+.** CI tests 3.10 to 3.14.
- **Code style:** [ruff](https://docs.astral.sh/ruff/) with the rules in `pyproject.toml` (pycodestyle, pyflakes, isort, bugbear, pyupgrade, bandit). Line length 120, single quotes.
- **ASCII-only source files.** Write non-ASCII characters in Python strings as `\uXXXX` / `\U000XXXXX` escapes. This keeps hidden characters out of the code of a tool that detects them, and CI's self-scan fails otherwise.
- **Escape attacker-controlled output.** Decoded payloads reach terminals, workflow logs and job summaries; any new output format must escape them for its medium (see `report.py`).
- **Workflows:** pin third-party actions to a full commit SHA with a version comment, and keep `permissions` minimal.
- **Dependencies for development** are pinned with hashes. To change them, edit `requirements-dev.in` and regenerate:
  `uv pip compile --universal --python-version 3.10 --generate-hashes requirements-dev.in -o requirements-dev.txt`.

## Releases

The maintainer publishes a GitHub release `vX.Y.Z`. The release workflow publishes to PyPI with trusted publishing and attaches Sigstore-signed files to the release. Versions follow [Semantic Versioning](https://semver.org/). The `v1` tag tracks the latest 1.x release for Action users.

By contributing you agree that your contribution is licensed under the [MIT License](LICENSE).
