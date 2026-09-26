# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

## [1.1.0] - 2026-09-26

### Added
- Python 3.14 support.
- Release assets (wheel and sdist) are attached to each GitHub release with Sigstore signatures (`*.sigstore.json`).

### Removed
- Python 3.9 support; it reached end of life in October 2025.

## [1.0.1] - 2026-09-25

### Fixed
- Shortened the Action description to under 125 characters so the Action can be listed on GitHub Marketplace.

## [1.0.0] - 2026-09-25

### Added
- Scanner for six categories of hidden Unicode: tags, variation selectors, bidi controls, zero-width, control and other invisible characters.
- Decoding of tag (ASCII smuggling) and variation-selector (byte smuggling) payloads in reports.
- Legitimate-use rules for emoji presentation, keycaps, emoji ZWJ sequences, non-Latin ZWNJ/ZWJ, subdivision flags and a leading BOM.
- CLI (`unicode-smuggling-guard`, alias `usguard`) with text and GitHub annotation output, `--ignore` and `--summary`.
- Composite GitHub Action with PR annotations and a job summary table.
- pre-commit hook.
