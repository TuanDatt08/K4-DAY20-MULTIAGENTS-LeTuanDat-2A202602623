# Báo cáo Lab: Self evolving Agentic

> Sao chép tệp này thành `report/REPORT.md` (đã làm ở Phần 0) và điền dần qua các Phần của lab. Xóa các dòng hướng dẫn dạng trích dẫn (bắt đầu bằng `>`). Văn phong kỹ thuật, ngắn gọn, mọi nhận định đi kèm số liệu hoặc bằng chứng. Trong buổi học: điền mục 1 đến 7 (bản nháp). Sau buổi học: hoàn thiện mục 8 đến 10.

## 1. Thông tin sinh viên và cấu hình

- Họ tên: Le Tuan Dat
- Mã sinh viên: 2A202602623

- Nhà cung cấp và mô hình: Google Gemini API, `LAB_MODEL=google_genai:gemini-3.5-flash-lite` (gói miễn phí). `LAB_TEMPERATURE=0` nhưng **bị bỏ qua**: thư viện cảnh báo model này dùng tham số lấy mẫu cố định, nên mỗi lần chạy có tính ngẫu nhiên. `recursion_limit` = 60 (mặc định).
- Phiên bản: `deepagents` 0.7.21, `langchain-google-genai` 4.4.0 (cài thêm bằng `pip install langchain-google-genai`, không có trong `pyproject.toml`). Máy Windows 11, chạy trong Docker (`python:3.12-slim`) theo `Dockerfile`.
- Số lần chạy tác vụ đã dùng / ngân sách: (cập nhật cuối) / 30
- Commit của tag `freeze`:

## 2. Giả thuyết (commit TRƯỚC tag `freeze`, Phần 4.0)

> Dự đoán điều kiện nào đạt điểm cao nhất trên **tác vụ đánh giá** và vì sao. Nêu căn cứ từ phân loại lỗi (mục 4) và từ tài liệu tham khảo. Điền cả ba dòng; `verify_freeze.py` kiểm tra điều này.

- H1 (subagents so với baseline):
- H2 (skills-auto so với baseline):
- H3 (tác vụ học so với tác vụ đánh giá):

## 3. Làm quen Deep Agents (Phần 0.3)

1. Công cụ tệp: `ls`, `read_file`, `write_file`, `edit_file`, `delete`, `glob`, `grep`; shell: `execute`; giao việc: `task`. Chỉ `execute` chạy được lệnh (Python, pytest...).
2. Subagent `general-purpose` dùng cho câu hỏi phức tạp, tìm tệp và tác vụ nhiều bước, *"has access to all tools as the main agent"*. Nó **không** thấy hội thoại của tác tử chính: *"Each invocation is stateless by default: the agent sees only the prompt you give it and returns a single final report"*. Vì vậy mọi quy tắc phải được ghi trong lời giao việc.
3. Từ `task`: *"Put full detail in the prompt and state exactly what it should return."* Từ `execute`: *"You MUST avoid using search commands like find and grep. Instead use the grep, glob tools to search."* Đáng chú ý: mô tả `execute` còn yêu cầu *"Use absolute paths and avoid `cd`"*, mâu thuẫn với quy ước đường dẫn tương đối `workspace/...` của lab. Đây là lý do `BASE_PROMPT`/`PATHS_NOTE` phải nhấn mạnh quy ước này (`/workspace` không tồn tại trong shell thật).

## 4. Đường cơ sở và phân loại lỗi (Phần 2.2)

> Chỉ dùng tác vụ học. Mỗi dòng là một check thất bại.

| Tác vụ | Check thất bại | Nhóm lỗi (A-G) | Bằng chứng (trích ngắn từ `detail` hoặc vết) |
|---|---|---|---|
| code-learn | `tests_not_modified` | A (qua subagent) | Đề bài: *"Do not modify the existing files in `tests/`"*. Tác tử chính giao cho `general-purpose`: *"Write comprehensive unit tests in a temporary test file or check all requirements..."*, **không chép quy tắc cấm sửa `tests/`**. Báo cáo của subagent: *"unit tests have been written and expanded in `workspace/tests/test_report.py`"*. Tác tử chính không kiểm tra lại (`subagent_calls`=1). |
| code-learn | `rule_type_hints` | E | *"RULE: every public function ... has type annotations on all parameters and on the return value."* |
| code-learn | `rule_regression_tests` | E | *"RULE: add tests/test_regressions.py with one test function per bug you fixed (at least 3)"* |
| code-learn | `rule_changelog` | E | *"RULE: record each fix in CHANGELOG.md under the heading '## Unreleased' as a bullet '- fix(<function name>): ...'"* |
| data-learn | `rule_money_in_cents` | E | *"RULE: money values in answer.json are integer cents (1606.67 USD is written 160667)."* |
| data-learn | `rule_meta_block` | E | *"RULE: answer.json has an object `meta` = {"source": ..., "rows_in": ..., "rows_used": ...}"* |
| data-learn | `rule_clean_csv` | E | *"RULE: write workspace/clean.csv with the header order_id,timestamp_utc,region,amount_cents ..."* |
| logs-learn | `rule_service_names` | E | *"RULE: service names in the output are lower-case with '-' replaced by '_'"* |
| logs-learn | `rule_sorted_errors` | E | *"RULE: `errors` is sorted by service, then by timestamp_utc, ascending."* |
| logs-learn | `rule_schema_header` | E | *"RULE: the top-level object has "schema_version": 2 and "generated_by": "log-triage"."* |

Nhận xét:

- **Nhóm E chiếm đa số: 9/10 check thất bại.** Đây là các quy ước của Acme mà đề bài không nêu, nên tác tử không thể tự biết. Đây chính là loại lỗi mà skill (tri thức thủ tục) có thể phòng ngừa: curator đọc `detail` (*"RULE: ..."*) và viết thành quy tắc.
- **Bằng chứng phủ định cho nhóm A–D** (`scripts/check_breakdown.py`): baseline đạt **17/18 check kỹ thuật**, nhưng chỉ **0/9 check quy ước**. Tác tử đã xử lý đúng dữ liệu bẩn (D), ví dụ data-learn đạt `duplicate_rows_removed`, `missing_amount_orders`. Nó cũng chạy lại test trước khi kết thúc (B), ví dụ code-learn chạy `pytest` 4 lần, lần cuối báo test pass. Lời kết của tác tử cũng không nhắc tới tệp không tồn tại (F).
- **Check kỹ thuật duy nhất bị fail** (`tests_not_modified`) do giao việc thiếu ngữ cảnh: tác tử chính tự gọi subagent mặc định nhưng không truyền ràng buộc của đề. Skill khó phòng lỗi này, vì subagent tự định nghĩa không thừa kế skill. Cách phòng đúng là ghi đủ quy tắc vào lời giao việc (đúng như `SUBAGENTS_NOTE` yêu cầu).
- Ghi chú hạ tầng: các lần chạy đầu tiên bị hỏng vì git trên Windows đổi tệp tác vụ sang CRLF. Workspace chưa sửa vẫn fail `tests_not_modified` khi ở dạng CRLF. Các lần chạy đó được tách ra `results/*-crlf-invalid/` và không dùng trong báo cáo.

## 5. Điều kiện `subagents` (Phần 2.3)

- Các subagent đã định nghĩa (`src/lab/subagents.py`), tách theo vòng đời "đọc, làm, kiểm":
  - `explorer`: chỉ đọc README, CHANGELOG, docstring và mẫu dữ liệu, rồi báo cáo đặc tả và quy ước; không sửa tệp.
  - `implementer`: sửa nguyên nhân gốc, chạy test sau mỗi thay đổi, báo cáo các tệp đã đổi.
  - `reviewer`: kiểm tra độc lập kết quả theo từng quy tắc và trường hợp biên; không sửa tệp.
  - `description` của mỗi subagent viết dạng *"Use BEFORE/AFTER..."* để tác tử chính biết khi nào gọi.
- `subagent_calls`:
  - **code-learn = 6**: `explorer` ×3, `implementer` ×2, `reviewer` ×1. Tác tử chính giao việc cho cả ba vai trò, nhưng gọi `explorer` 3 lần liên tiếp với yêu cầu gần trùng nhau (lần 3: *"Read the exact contents of ..."*). Đây là dấu hiệu tác tử chính không tin báo cáo tóm tắt và phải hỏi lại, gây thừa chi phí.
  - **data-learn, logs-learn: (chưa có, chạy lại sau lỗi 429)**
- Thông tin thiếu khi giao việc:
  - Không lời giao việc nào chép quy tắc *"Do not modify the existing files in `tests/`"* của đề. Lời giao cho `implementer` chỉ ghi *"Implement fixes for parse_price, apply_discount, low_stock, and to_csv_row according to their docstring specifications..."*, và check `tests_not_modified` vẫn fail như ở baseline.
  - `reviewer` được gọi (*"Run pytest and check git status/diff..."*), nhưng không được giao danh sách quy tắc của đề, nên không phát hiện vi phạm.
  - Kết luận: `SUBAGENTS_NOTE` yêu cầu *"put ALL the task rules ... in the delegation message"*, nhưng tác tử chính không làm theo.
- Token và thời gian (code-learn): `subagents` 370,275 token / 206.8 s so với `baseline` 342,181 token / 154.6 s (**+8% token, +34% thời gian**), cùng điểm 6/10. Số `tool_calls` của luồng chính giảm (10 so với 25) vì công việc chuyển vào subagent, nhưng token vẫn được tính đủ nhờ `UsageMetadataCallbackHandler`.

## 6. Self-evolving: skill do curator sinh (Phần 3)

- Số lần chạy curator, số skill bị xóa và lý do:

| Skill | Tổng quát hay riêng cho tác vụ học? | Đúng hay sai (nêu chỗ sai nếu có) | Độ dài, `description` và `skills_read` ở Phần 3.4 |
|---|---|---|---|
| | | | |

## 7. Kết quả so sánh (Phần 4.3, 4.4)

> Dán nội dung `report/table.md` và kết quả `python scripts/check_breakdown.py`. Nêu các lần chạy có `error` hoặc `skills_modified = true` (nếu có) và cách xử lý.

```text
(dán bảng ở đây)
```

## 8. Phân tích

> Trả lời từng câu bằng số liệu từ mục 7 và bằng chứng từ vết. Kết quả âm hoặc không có khác biệt vẫn hợp lệ nếu được phân tích tốt.

1. So với `baseline`, điều kiện nào cải thiện điểm tác vụ **học**? Điều kiện nào cải thiện điểm tác vụ **đánh giá**? Có điều kiện nào cải thiện tác vụ học nhưng không cải thiện tác vụ đánh giá? Nếu có, đó là dấu hiệu gì?
2. Tách điểm thành check kỹ thuật và check quy ước (`rule_`). Skill do curator sinh giúp nhóm check nào? Check quy ước **mới** của tác vụ đánh giá có được skill giúp không, và vì sao?
3. Dựa vào vết và `skills_read`, giải thích một check mà skill giúp đạt và một check mà skill không giúp (skill chưa được đọc, đọc nhưng không làm theo, skill thiếu hoặc sai).
4. Chi phí: so sánh số token trung bình giữa các điều kiện. Điều kiện nào có hiệu quả tốt nhất theo điểm trên mỗi token? Đa tác tử có đáng chi phí trong thí nghiệm này không?
5. Có dấu hiệu rò rỉ dữ liệu hoặc quá khớp nào trong skill sinh ra không? Bạn đã phòng tránh như thế nào?
6. Nhiễu: so sánh điểm tác vụ học của cùng bộ skill ở Phần 3.4 (đã sao lưu) và sau đóng băng. Chênh lệch bao nhiêu? Nó cho biết điều gì về độ tin cậy của các chênh lệch trong bảng ở mục 7?

## 9. Hạn chế và tính hợp lệ

> Nêu ít nhất 3 hạn chế và ảnh hưởng của từng hạn chế đến kết luận (ví dụ: chỉ 3 tác vụ mỗi vai trò, mỗi cấu hình chạy một lần, nhiễu của mô hình, tác vụ do giảng viên thiết kế sẵn quy ước, chỉ một mô hình).

1.
2.
3.

## 10. Kết luận

> Tối đa 5 câu. Chỉ khẳng định điều số liệu hỗ trợ. Nêu một đề xuất cải tiến tiếp theo.

## Phụ lục

- Lệnh đã chạy (theo thứ tự, trong container Docker):
  1. `docker build -t lab-deepagents .` và `docker run -it --name lab --env-file .env -v "%cd%:/lab" lab-deepagents`; trong container: `apt-get install -y git`, `pip install langchain-google-genai`.
  2. `pytest tests/test_01_provided.py` → 15 passed; `python scripts/tour.py`.
  3. Cài đặt `subagents.py`, `agent.py`, `runner.py`, `curator.py` → `pytest` → **32 passed** (test_01: 15, test_02: 9, test_03: 6, test_04: 2).
  4. Lần chạy đầu (`baseline` và `subagents` trên tác vụ học) → **không hợp lệ** do CRLF (xem ghi chú), lưu ở `results/*-crlf-invalid/`.
  5. Sửa xuống dòng về LF, `git config core.autocrlf false`, sửa lại commit `implement harness` (chỉ còn 4 tệp mã và REPORT.md).
  6. `export PYTHONWARNINGS=ignore`; `python -m lab.runner --condition baseline --tasks learn` → code-learn 6/10 (342,181 tok), data-learn 5/8 (250,903 tok), logs-learn 6/9 (71,373 tok).
  7. `python -m lab.runner --condition subagents --tasks learn` → code-learn 6/10 (370,275 tok); data-learn và logs-learn lỗi `429 RESOURCE_EXHAUSTED` (hạn mức miễn phí 500 request/ngày), cần chạy lại.
  8. `python scripts/check_breakdown.py` → baseline learn: kỹ thuật 17/18, quy ước 0/9.
- Thử thách mở rộng (nếu có): không làm.
- Ghi chú khác:
  - **CRLF:** git trên Windows (`core.autocrlf=true`) đổi các tệp tác vụ sang CRLF khi checkout. Kiểm chứng bằng `grade()`: workspace `code-learn` chưa sửa đạt `tests_not_modified` ở dạng LF nhưng fail ở dạng CRLF. Mọi lần chạy trước khi sửa bị loại khỏi phân tích.
  - **Hạn mức API:** gói miễn phí của Gemini giới hạn 500 request/ngày/model; một lần chạy dùng khoảng 40–60 request (`subagents` nhiều hơn). Lỗi 429 là lỗi hạ tầng, không tính là lỗi tác tử; các lần chạy đó được chạy lại.
  - **Nhiệt độ:** `gemini-3.5-flash-lite` bỏ qua `temperature=0`, nên kết quả có nhiễu giữa các lần chạy.
