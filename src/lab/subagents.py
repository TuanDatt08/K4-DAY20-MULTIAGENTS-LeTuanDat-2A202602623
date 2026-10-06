"""GUIDE Phần 1 - Định nghĩa subagent (tác tử con).   >>> SINH VIÊN CÀI ĐẶT <<<

Pseudo-code: guides/pseudocode/02_subagents.md
Kiểm tra:    pytest tests/test_02_agent.py
"""


def get_subagents() -> list[dict]:
    """Trả về danh sách subagent (ít nhất 2, tên khác nhau).

    Mỗi phần tử là một dict có các khóa bắt buộc:
      "name":          tên duy nhất (chữ thường, có thể có dấu gạch ngang)
      "description":   khi nào tác tử chính nên giao việc cho subagent này (viết như một hướng dẫn hành động)
      "system_prompt": chỉ dẫn cho subagent
    Gợi ý vai trò: explorer (đọc và báo cáo), implementer (thực hiện), reviewer (kiểm tra độc lập).
    """
    return [
        {
            "name": "explorer",
            "description": "Use BEFORE changing anything: reads README, CHANGELOG, docstrings, the instructions and samples "
                           "of the data/log files, and reports the exact specs, formats, conventions and edge cases found.",
            "system_prompt": "You are a read-only explorer. Read every spec file (README, CHANGELOG, docstrings) and sample "
                             "the data. Report facts only: required output files, keys and formats, organisational "
                             "conventions, dirty values (duplicates, missing values, mixed date formats, time zones). "
                             "Never modify any file.",
        },
        {
            "name": "implementer",
            "description": "Use to make the actual change (fix code, write a script, produce the output files) once the "
                           "rules are known; put ALL task rules and file paths in the delegation message.",
            "system_prompt": "You implement exactly what you are asked. Fix root causes in shared functions, not symptoms. "
                             "Run the tests or your script after every change and report the commands you ran, their "
                             "output, and every file you created or changed.",
        },
        {
            "name": "reviewer",
            "description": "Use AFTER the work is done to independently verify the result against every task rule and "
                           "edge case before giving the final answer.",
            "system_prompt": "You are an independent reviewer. Re-run the tests, open each output file and check it against "
                             "every rule you were given (file names, keys, formats, conventions, edge cases). Report each "
                             "violation precisely. Do not modify files.",
        },
    ]
