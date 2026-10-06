"""GUIDE Phần 3 - Người tuyển chọn skill (skill curator): tự viết skill từ các lần chạy thất bại.   >>> SINH VIÊN CÀI ĐẶT curate_skills <<<

Pseudo-code: guides/pseudocode/04_curator.md
Kiểm tra:    pytest tests/test_04_curator.py
Chạy thật:   python -m lab.curator
"""
import json
import re
from pathlib import Path

from .tasks import ROOT, eval_markers   # có sẵn: định danh của tác vụ đánh giá, tính lúc chạy

# ---- CÓ SẴN, KHÔNG SỬA: kiểm tra và tách khối skill (phần dễ sai và liên quan bảo mật) ----------------
SAFE_NAME = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


def validate_skill(text: str, expected_name: str | None = None) -> list[str]:
    """Kiểm tra nội dung một SKILL.md. Trả về danh sách vấn đề (rỗng = hợp lệ).

    Quy tắc: có khối YAML frontmatter; `name` chữ thường/số/gạch ngang (tối đa 64 ký tự) và bằng `expected_name`
    nếu được truyền; có `description` (tối đa 1024 ký tự); phần thân tối đa 80 dòng; không chứa chuỗi nào của
    `eval_markers()`. Quy tắc về `name` cũng là biện pháp bảo mật: tên khối do LLM sinh ra được dùng để tạo
    đường dẫn, nên `../evil` không được lọt qua.
    """
    problems = []
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text.strip() + "\n", re.S)
    if not m:
        return ["missing YAML frontmatter"]
    front, body = m.groups()
    name = re.search(r"^name:\s*(.+)$", front, re.M)
    desc = re.search(r"^description:\s*(.+)$", front, re.M)
    n = name.group(1).strip() if name else ""
    if not SAFE_NAME.fullmatch(n) or len(n) > 64:
        problems.append("invalid name")
    elif expected_name is not None and n != expected_name:
        problems.append("name differs from the block name")
    if not desc or len(desc.group(1).strip()) > 1024:
        problems.append("missing or too long description")
    if len(body.strip().splitlines()) > 80:
        problems.append("body longer than 80 lines")
    low = text.lower()
    for marker in eval_markers():
        if marker in low:
            problems.append(f"mentions evaluation material: {marker}")
    return problems


def parse_skill_blocks(reply: str) -> list[tuple[str, str]]:
    """Tách câu trả lời của LLM thành danh sách (name, nội dung SKILL.md).

    Khuôn dạng: `=== SKILL: <name> ===` ... `=== END ===`. Một khối kết thúc ở điểm nào đến trước trong ba điểm:
    `=== END ===`, tiêu đề `=== SKILL:` kế tiếp, hoặc cuối văn bản (LLM đôi khi quên dòng END).
    """
    pattern = re.compile(r"^=== SKILL: (\S+) ===[ \t]*\n(.*?)(?=^=== END ===|^=== SKILL: |\Z)", re.S | re.M)
    return [(name, text.strip()) for name, text in pattern.findall(str(reply))]
# --------------------------------------------------------------------------------------------------


PROMPT = """You write SKILLS for a coding and data-analysis agent.
Below are the failed checks (name and the review bot's feedback) and the end of the execution trace of several runs.
Find the general PROCESS mistakes and organisational conventions behind them (not specific answers) and write at most
{max_skills} short skills that prevent them on NEW tasks of the same kind.

Rules:
- Skills must be general: no task ids, no file, function or column names specific to one task, no values computed
  from a task's data.
- The organisational conventions in the feedback (lines starting with "RULE:") are not stated in task instructions, so
  a vague skill ("use the required heading") is useless. Copy every convention PRECISELY: exact output file names,
  headings, bullet formats, JSON keys and constant values, units, casing and sort orders. These are rules, not answers.
- Each skill has YAML frontmatter with `name` (lowercase letters, digits and hyphens) and `description` (one sentence
  starting with "Use when ..." that names the broad kind of task), then at most 40 lines of imperative instructions
  (a numbered checklist ending with a self-check works well).
- Output format, exactly:
=== SKILL: <name> ===
---
name: <name>
description: <when to use>
---
<body>
=== END ===

{runs}"""


def curate_skills(results_dir="results", source_condition="baseline", out_dir=None, model=None, max_skills: int = 3) -> list[Path]:
    """Đọc các lần chạy của TÁC VỤ HỌC (role == "learn") trong `source_condition`, nhờ LLM viết skill, ghi file.

    Các bước: nạp run.json + trace.md -> (nếu không có check nào thất bại: in cảnh báo và trả về [] mà KHÔNG gọi LLM)
    -> dựng prompt -> model.invoke(prompt) -> parse_skill_blocks -> validate_skill(text, expected_name=name)
    -> ghi `<out_dir>/<name>/SKILL.md`. Mặc định `out_dir` = <gốc lab>/skills/auto (dùng `ROOT` từ lab.tasks).
    Giữ tối đa `max_skills` skill hợp lệ; skill không hợp lệ bị bỏ qua.
    Prompt chứa, với mỗi check thất bại, TÊN và trường `detail` (lời nhận xét của bot đánh giá: phát biểu quy tắc bị vi phạm)
    cùng phần cuối của vết (trace). Với tác vụ học, `detail` chỉ phát biểu quy tắc, không chứa đáp án.
    Tuyệt đối KHÔNG đưa dữ liệu của tác vụ đánh giá (role == "eval") vào prompt.
    model mặc định: make_model() (lab.model).
    Trả về: danh sách đường dẫn SKILL.md đã ghi.
    """
    out_dir = Path(out_dir) if out_dir else ROOT / "skills" / "auto"
    runs = []
    for f in sorted(Path(results_dir, source_condition).glob("*/run.json")):
        r = json.loads(f.read_text(encoding="utf-8"))
        if r.get("role") != "learn":
            continue                                          # never use evaluation data
        tr = f.with_name("trace.md")
        trace = tr.read_text(encoding="utf-8")[-6000:] if tr.exists() else ""
        failed = [(c["name"], c.get("detail", "")) for c in r.get("checks", []) if not c.get("passed")]
        runs.append({"task": r["task"], "failed": failed, "trace": trace})
    if not any(r["failed"] for r in runs):
        print("WARNING: no failed checks in the learning runs; nothing to curate")
        return []

    text = "\n\n".join(
        f"## Run: {r['task']}\nFailed checks:\n" + "\n".join(f"- {n}: {d}" for n, d in r["failed"])
        + f"\nTrace (end):\n{r['trace']}"
        for r in runs if r["failed"])
    if model is None:
        from .model import make_model
        model = make_model()
    reply = model.invoke(PROMPT.format(max_skills=max_skills, runs=text)).text   # .text: content may be a block list

    written = []
    for name, skill in parse_skill_blocks(reply):
        problems = validate_skill(skill, expected_name=name)
        if len(written) >= max_skills or problems:
            print(f"skipped {name!r}: {problems or 'max_skills reached'}")
            continue
        path = out_dir / name / "SKILL.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(skill + "\n", encoding="utf-8")
        written.append(path)
    return written


if __name__ == "__main__":
    for p in curate_skills():
        print("wrote", p)
