---
name: coding-standards-and-testing
description: Use when modifying codebases, fixing bugs, or implementing package features that require strict adherence to repository rules, type hints, regression tests, and changelogs.
---
<body>
1. Check for existing testing frameworks, CI configurations, and git repositories before making changes.
2. Never modify files inside test directories unless explicitly permitted (add new test files instead).
3. Add full type annotations to all parameters and return values for every public function (names not starting with `_`).
4. Write regression tests for every bug fixed, placing them in the specified test file, and run the test suite to verify success.
5. Record every fix in the changelog under the required heading using the precise bullet format specified by project conventions.
6. Self-check: Are all new/modified functions typed, all rules/constraints met, tests passing, and the changelog updated?
