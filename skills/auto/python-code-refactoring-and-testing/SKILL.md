---
name: python-code-refactoring-and-testing
description: Use when fixing bugs, refactoring Python packages, or adding tests and changelog entries.
---
1. Never modify or delete any original files inside `tests/` or source directories unless explicitly instructed (new test files are allowed).
2. Ensure every public function (name not starting with `_`) has complete type annotations on all parameters and on the return value.
3. Add regression tests in `tests/test_regressions.py` with at least one test function per fixed bug (at least 3 total); verify the entire test suite passes.
4. Record each fix in `CHANGELOG.md` under the heading `## Unreleased` as a bullet: `- fix(<function name>): <short description>` (at least 3 bullets).
5. Self-check: Run `pytest` with `PYTHONPATH` set to the package root and verify git status / file contents before finishing.
