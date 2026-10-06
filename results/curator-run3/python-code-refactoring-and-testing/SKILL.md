---
name: python-code-refactoring-and-testing
description: Use when refactoring Python packages, adding type hints, fixing bugs, and writing regression tests.
---
1. Never modify or delete any original files inside `tests/` directories; add new test files instead.
2. Add type annotations to all parameters and return values for every public function (names not starting with `_`).
3. Add a regression test file (`tests/test_regressions.py`) containing at least one test function per bug fixed (minimum 3 tests total) and ensure pytest passes.
4. Record each fix in `CHANGELOG.md` under the exact heading `## Unreleased` as a bullet formatted precisely as: `- fix(<function name>): <short description>` (at least 3 bullets).
5. Self-check: Run pytest and check git status/diff to verify all constraints are satisfied before finishing.
