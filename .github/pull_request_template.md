## Summary

<!-- What does this change and why? Link the issue: Fixes #123 -->

## Checklist

- [ ] Failing test written first, then the change
- [ ] `python -m ruff check .` and `python -m pytest` pass
- [ ] The repo still scans clean with `python -m unicode_smuggling_guard .`
- [ ] Source files are ASCII-only (non-ASCII written as `\uXXXX` escapes)
- [ ] No new runtime dependencies
- [ ] CHANGELOG entry under `[Unreleased]` for user-visible changes
