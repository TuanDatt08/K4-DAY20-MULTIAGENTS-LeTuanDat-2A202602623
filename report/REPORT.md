# Báo cáo Lab: Self evolving Agentic

## 1. Thông tin sinh viên và cấu hình

- Họ tên: Le Tuan Dat
- Mã sinh viên: 2A202602623

- Nhà cung cấp và mô hình: Google Gemini API, `LAB_MODEL=google_genai:gemini-3.5-flash-lite` (gói miễn phí). `LAB_TEMPERATURE=0` nhưng **bị bỏ qua**: thư viện cảnh báo model này dùng tham số lấy mẫu cố định, nên mỗi lần chạy có tính ngẫu nhiên. `recursion_limit` = 60 (mặc định).
- Phiên bản: `deepagents` 0.7.21, `langchain-google-genai` 4.4.0 (cài thêm bằng `pip install langchain-google-genai`, không có trong `pyproject.toml`). Máy Windows 11, chạy trong Docker (`python:3.12-slim`) theo `Dockerfile`.
- Số lần chạy tác vụ đã dùng / ngân sách: 27 / 30 (gồm 6 lần không hợp lệ do CRLF, 4 lần lỗi hạ tầng và 1 lần bị ngắt), cùng 3 lần gọi curator.
- Commit của tag `freeze`: `8954721` (commit `hypotheses`: `0000d67`).

## 2. Giả thuyết (commit TRƯỚC tag `freeze`, Phần 4.0)

- H1 (subagents so với baseline): Trên tác vụ đánh giá, `subagents` **không cao điểm hơn** `baseline` (chênh lệch trong khoảng ±1 check mỗi tác vụ), nhưng tốn **khoảng 1,1–4 lần token**. Căn cứ: trên tác vụ học, hai điều kiện cùng điểm (code 6/10, logs 6/9) trong khi token tăng 8% và 3,7 lần. Lỗi chủ yếu là nhóm E (quy ước không có trong đề), mà chia việc không cung cấp thêm quy ước nào. Bài viết của Anthropic về hệ thống nghiên cứu đa tác tử cũng ghi nhận chi phí token khoảng 15 lần so với hội thoại thường.
- H2 (skills-auto so với baseline): `skills-auto` **cao hơn** `baseline` trên tác vụ đánh giá của họ `code` và `logs`. Mức tăng đến từ các check `rule_` đã học, vì skill chép chính xác các quy ước Acme mà tác vụ đánh giá dùng lại. **Không cải thiện** họ `data` (không có skill nào qua được bộ lọc) và **không giúp** quy ước mới chỉ có ở tác vụ đánh giá. Check kỹ thuật giữ nguyên (baseline đã đạt 17/18). Điều kiện để giả thuyết đúng: tác tử thực sự đọc skill (`skills_read` > 0) và làm theo. SkillsBench ghi nhận skill do mô hình tự sinh trung bình không có lợi, nên mức tăng có thể nhỏ hoặc bằng 0 nếu skill không được đọc.
- H3 (tác vụ học so với tác vụ đánh giá): Mức tăng nhờ skill trên **tác vụ học lớn hơn** trên tác vụ đánh giá, vì skill được rút từ chính phản hồi của tác vụ học, còn tác vụ đánh giá có dữ liệu khác và một quy ước mới (dấu hiệu quá khớp theo SkillEvolBench). Do model bỏ qua `temperature`, chênh lệch nhỏ hơn hoặc bằng 1 check mỗi tác vụ nên được coi là nhiễu.

## 3. Làm quen Deep Agents (Phần 0.3)

1. Công cụ tệp: `ls`, `read_file`, `write_file`, `edit_file`, `delete`, `glob`, `grep`; shell: `execute`; giao việc: `task`. Chỉ `execute` chạy được lệnh (Python, pytest...).
2. Subagent `general-purpose` dùng cho câu hỏi phức tạp, tìm tệp và tác vụ nhiều bước, *"has access to all tools as the main agent"*. Nó **không** thấy hội thoại của tác tử chính: *"Each invocation is stateless by default: the agent sees only the prompt you give it and returns a single final report"*. Vì vậy mọi quy tắc phải được ghi trong lời giao việc.
3. Từ `task`: *"Put full detail in the prompt and state exactly what it should return."* Từ `execute`: *"You MUST avoid using search commands like find and grep. Instead use the grep, glob tools to search."* Đáng chú ý: mô tả `execute` còn yêu cầu *"Use absolute paths and avoid `cd`"*, mâu thuẫn với quy ước đường dẫn tương đối `workspace/...` của lab. Đây là lý do `BASE_PROMPT`/`PATHS_NOTE` phải nhấn mạnh quy ước này (`/workspace` không tồn tại trong shell thật).

## 4. Đường cơ sở và phân loại lỗi (Phần 2.2)

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
  - **logs-learn = 4**: `explorer` ×2, `implementer` ×1, `reviewer` ×1. Lần này lời giao việc cho `implementer` liệt kê đầy đủ các quy tắc của đề (*"strictly according to all rules: 1. Filter: include only entries whose level is ERROR or CRITICAL ... 2. timestamp_utc: converted to UTC ..."*). Nhờ vậy 6/6 check kỹ thuật đạt, nhưng 3 check `rule_` vẫn fail giống baseline, vì quy ước không có trong đề nên tác tử chính không thể truyền đi.
  - **data-learn**: lần chạy bị lỗi hạ tầng (lần 1: `429 RESOURCE_EXHAUSTED`; lần 2: `RemoteProtocolError: Server disconnected`), không dùng để phân tích.
  - **code-eval = 3**: `explorer` ×2, `implementer` ×1. Đạt 7/11, bằng baseline; cùng fail 4 check `rule_`.
  - **data-eval = 7**: `explorer` ×1, rồi 3 vòng `implementer` → `reviewer` liên tiếp. `reviewer` phát hiện sai, nhưng lời giao việc sửa lỗi chỉ ghi *"Fix the script to correctly calculate march_orders_utc and all required keys"*, không truyền định nghĩa hay quy tắc múi giờ của đề. Sau 3 vòng, check kỹ thuật `march_orders_utc` vẫn fail (baseline đạt). Đây là ví dụ rõ về **mất thông tin khi giao việc**: mỗi subagent bắt đầu lại từ đầu, chỉ thấy lời giao việc ngắn.
  - **logs-eval**: lần chạy bị ngắt thủ công (Ctrl+C) do chạy quá lâu sát hạn nộp; không có kết quả.
- Thông tin thiếu khi giao việc:
  - Không lời giao việc nào chép quy tắc *"Do not modify the existing files in `tests/`"* của đề. Lời giao cho `implementer` chỉ ghi *"Implement fixes for parse_price, apply_discount, low_stock, and to_csv_row according to their docstring specifications..."*, và check `tests_not_modified` vẫn fail như ở baseline.
  - `reviewer` được gọi (*"Run pytest and check git status/diff..."*), nhưng không được giao danh sách quy tắc của đề, nên không phát hiện vi phạm.
  - Kết luận: `SUBAGENTS_NOTE` yêu cầu *"put ALL the task rules ... in the delegation message"*, nhưng tác tử chính không làm theo.
- Token và thời gian, cùng điểm ở cả hai tác vụ:
  - code-learn: `subagents` 370,275 token / 206.8 s so với `baseline` 342,181 token / 154.6 s (**+8% token, +34% thời gian**), cùng 6/10.
  - logs-learn: `subagents` 262,825 token / 118.7 s so với `baseline` 71,373 token / 51.8 s (**gấp 3,7 lần token**), cùng 6/9.
  - code-eval: 288,430 token / 224.7 s so với 147,987 token / 94.7 s (**gấp 1,9 lần**), cùng 7/11.
  - data-eval: 767,971 token / 422.8 s so với 79,078 token / 35.0 s (**gấp 9,7 lần**), điểm thấp hơn (4/9 so với 5/9). Số `tool_calls` của luồng chính giảm (10 so với 25) vì công việc chuyển vào subagent, nhưng token vẫn được tính đủ nhờ `UsageMetadataCallbackHandler`.

## 6. Self-evolving: skill do curator sinh (Phần 3)

- Số lần chạy curator: **3** (1 lần đầu và 2 lần chạy lại, đúng giới hạn).
  - **Lần 1** sinh `coding-standards-and-testing` và `strict-schema-output-compliance` (lưu ở `results/curator-run1/`). Cả hai bị **xóa** vì quá mơ hồ: chỉ ghi *"under the required heading"*, *"in the specified test file"*, *"Include all required metadata blocks"* mà không nêu quy ước cụ thể. Quy ước Acme không có trong đề, nên skill như vậy không giúp tác tử biết phải làm gì. Nguyên nhân: prompt của curator cấm *"no answers or numbers"*, khiến model né cả tên quy ước. Prompt được sửa để yêu cầu chép chính xác các dòng `RULE:` (tên tệp, heading, khóa JSON), nhưng vẫn cấm giá trị tính từ dữ liệu tác vụ. Không sửa tay nội dung skill.
  - **Lần 2** (bộ skill được chốt và đóng băng): sinh 3 skill. `validate_skill` **từ chối** skill dữ liệu `data-cleaning-and-json-export` vì *"mentions evaluation material: orders"*. Giữ 2 skill bên dưới.
  - **Lần 3** (ghi ra `results/curator-run3/`, không dùng): skill dữ liệu lại bị từ chối với cùng lý do; 2 skill còn lại gần trùng lần 2 nên không thay.
  - Hệ quả: họ `data` **không có skill nào**. Từ "orders" là từ thông dụng trong quy tắc của data-learn (*"one row per distinct order"*), nhưng cũng là tên tệp của tác vụ đánh giá, nên bộ lọc rò rỉ chặn cả skill hợp lệ (dương tính giả). Đây là đánh đổi giữa an toàn và hữu ích.

| Skill | Tổng quát hay riêng cho tác vụ học? | Đúng hay sai (nêu chỗ sai nếu có) | Độ dài, `description` và `skills_read` ở Phần 3.4 |
|---|---|---|---|
| `python-code-refactoring-and-testing` | Tổng quát cho mọi tác vụ sửa gói Python. Không nêu tên hàm hay tệp của workspace; chỉ có tên do quy ước Acme yêu cầu (`tests/test_regressions.py`, `CHANGELOG.md`, `## Unreleased`, `- fix(<function name>): ...`). | Đúng: khớp từng `detail` của 4 check thất bại ở code-learn (cấm sửa `tests/`, type hints, regression tests, changelog). Bước 5 (*"Run pytest with PYTHONPATH set to the package root"*) hợp lý nhưng hơi thừa. | 9 dòng, 5 bước, có tự kiểm tra. `description` *"Use when fixing bugs, refactoring Python packages, or adding tests and changelog entries"*: rộng, đúng tình huống kích hoạt. `skills_read` ở Phần 3.4: không chạy (bỏ để tiết kiệm hạn mức API). |
| `log-parsing-and-json-formatting` | Phần lớn tổng quát (service name, thứ tự sắp xếp, header `schema_version`/`generated_by` là quy ước Acme). Bước 4 nêu cú pháp `-- last message repeated N times --` lấy từ log học, hơi **riêng cho tác vụ học** (nguy cơ quá khớp nếu log mới dùng cú pháp khác). | Đúng với 3 `detail` của logs-learn. Không thấy hướng dẫn gây hại. | 9 dòng. `description` *"Use when parsing log files, extracting structured errors, and formatting JSON outputs"*: đúng tình huống. `skills_read`: như trên. |

## 7. Kết quả so sánh (Phần 4.3, 4.4)

`report/table.md` (sinh bởi `python -m lab.compare`):

| Task | baseline | subagents | skills-auto |
|---|---|---|---|
| code-learn | 6/10 | 6/10 | 9/10 |
| data-learn | 5/8 | 0/8 | 5/8 |
| logs-learn | 6/9 | 6/9 | 9/9 |
| code-eval | 7/11 | 7/11 | 1/11 |
| data-eval | 5/9 | 4/9 | 5/9 |
| logs-eval | 6/10 | - | 9/10 |
| **Mean score - learning tasks** | 0.63 | 0.42 | 0.84 |
| **Mean score - evaluation tasks** | 0.60 | 0.54 | 0.52 |
| **Mean tokens per run** | 157,653 | 409,391 | 128,247 |
| **Runs that read a skill** | 0/6 | 0/5 | 6/6 |

`python scripts/check_breakdown.py`:

```text
condition     role    technical  house rules  mean tokens  read a skill
baseline      eval     18/18         0/12          93,820      0/3
baseline      learn    17/18         0/9          221,485      0/3
subagents     eval     11/12         0/8          528,200      0/2
subagents     learn    12/18         0/9          330,185      0/3
skills-auto   eval     12/18         3/12          76,300      3/3
skills-auto   learn    17/18         6/9          180,194      3/3
```

`python scripts/verify_freeze.py` → `checked 6 runs of skill conditions: OK`. Không lần chạy nào có `skills_modified = true`.

Các lần chạy có `error` hoặc bất thường:

- `subagents/data-learn` (0/8): `RemoteProtocolError: Server disconnected` (lỗi hạ tầng; lần trước đó là `429`). Điểm 0/8 không phản ánh tác tử; loại khỏi phân tích. Trung bình `subagents` học tính lại trên 2 tác vụ hợp lệ: (6/10 + 6/9)/2 = **0.63**, bằng baseline. Tương tự, `subagents learn` kỹ thuật 12/18 bao gồm 5 check fail của lần chạy lỗi này; trên 2 tác vụ hợp lệ là 12/13.
- `baseline/code-eval`: lần chạy đầu gặp `RemoteProtocolError` giữa chừng (7/11, vết rỗng); đã **chạy lại** theo hướng dẫn của GUIDE, lần chạy lại hợp lệ, cũng 7/11 (24 tool call). Bảng dùng lần chạy lại.
- `skills-auto/code-eval` (1/11): **không có `error`**. Vết cho thấy tác tử đọc cả 2 skill và mọi tệp nguồn, rồi ở bước thứ 15 model trả về một thông điệp suy biến (nội dung văn bản chỉ là `"ass"`) và kết thúc mà không sửa tệp nào. 1/11 bằng điểm của workspace chưa sửa. Đây là lỗi của model (một mẫu ngẫu nhiên hỏng), không phải do skill chỉ dẫn sai, nhưng vẫn là một lần chạy hợp lệ nên được giữ nguyên trong bảng.
- `subagents/logs-eval`: **không có kết quả**. Lần chạy bị ngắt thủ công (Ctrl+C) vì kéo dài sát hạn nộp; trung bình `subagents` trên tác vụ đánh giá (0.54) chỉ tính 2 tác vụ.

## 8. Phân tích

1. **Cải thiện tác vụ học và tác vụ đánh giá.**
   - Tác vụ học: `skills-auto` cải thiện (0.63 → 0.84). code-learn 6 → 9/10, logs-learn 6 → 9/9, data-learn giữ 5/8. `subagents` không cải thiện (0.63 trên 2 tác vụ hợp lệ, bằng baseline).
   - Tác vụ đánh giá, xét trung bình: `skills-auto` **thấp hơn** baseline (0.52 so với 0.60). Nhưng chênh lệch này do một lần chạy suy biến (code-eval 1/11, xem mục 7).
   - Tác vụ đánh giá, xét từng tác vụ: logs-eval tăng rõ (6 → 9/10), data-eval không đổi (5/9), code-eval không kết luận được.
   - `subagents` trên tác vụ đánh giá (2 tác vụ): 0.54, thấp hơn baseline trên cùng 2 tác vụ ((7/11 + 5/9)/2 = 0.60). code-eval bằng nhau (7/11); data-eval kém hơn 1 check kỹ thuật (`march_orders_utc`), do mất thông tin khi giao việc (mục 5).
   - Như vậy `skills-auto` cải thiện tác vụ học nhiều hơn tác vụ đánh giá: +0.21 so với −0.08 (hoặc +0.15 nếu bỏ code-eval). Đây là dấu hiệu **chuyển giao một phần**: lợi ích chuyển sang tác vụ đánh giá chỉ ở họ có skill và có quy ước dùng lại (logs). Kết quả phù hợp với H3, và không đủ dữ liệu để khẳng định H2 cho họ code.
2. **Check kỹ thuật so với check quy ước.**
   - Skill chỉ giúp nhóm **check quy ước**: tác vụ học 0/9 → 6/9, tác vụ đánh giá 0/12 → 3/12.
   - Check kỹ thuật không tăng: tác vụ học 17/18 ở cả hai điều kiện. Tác vụ đánh giá 18/18 → 12/18, và 6 check giảm đều thuộc lần chạy code-eval suy biến.
   - Các check quy ước **mới** của tác vụ đánh giá (`rule_version_bump`, `rule_sorted_keys_format`, `rule_source_line`) **đều fail** ở cả hai điều kiện. Skill chỉ chứa quy ước rút từ phản hồi của tác vụ học, nên không thể biết quy ước chưa từng xuất hiện. Đây là giới hạn cơ bản của việc tiến hóa từ phản hồi.
3. **Một check skill giúp đạt và một check skill không giúp.**
   - **Giúp:** `rule_schema_header` ở logs-eval. Ở `skills-auto` (`skills_read` = 1), tác tử đọc `skills/log-parsing-and-json-formatting/SKILL.md` ngay bước đầu; vết sau đó có `"schema_version": 2`, `"generated_by": "log-triage"` và `payment_service`, nên check đạt. Vết baseline không có chuỗi nào trong số này, nên check fail.
   - **Không giúp:**
     - `rule_money_in_cents` ở data-learn và data-eval. Tác tử có đọc skill (`skills_read` = 2, đọc cả skill code lẫn logs), nhưng không skill nào chứa quy ước tiền tệ, vì skill dữ liệu đã bị `validate_skill` chặn (mục 6). Lỗi thuộc loại **skill thiếu**.
     - `low_stock_follows_docstring` ở code-learn: là check kỹ thuật, baseline đạt nhưng `skills-auto` lại fail. Đây có thể là nhiễu, hoặc do tác tử tập trung vào checklist quy ước mà bỏ sót docstring.
4. **Chi phí.**
   - Token trung bình trên tác vụ học: baseline 221,485; `subagents` 330,185 (gấp 1.5 lần, nếu chỉ tính 2 lần chạy hợp lệ thì 316,550); `skills-auto` 180,194 (−19%).
   - Điểm trên 100k token (tác vụ học): baseline 0.28; `skills-auto` 0.47. `skills-auto` hiệu quả nhất, vì skill cho tác tử một checklist rõ ràng nên ít bước dò hơn (ví dụ logs-learn 7 tool call so với 9).
   - Tác vụ đánh giá: baseline 93,820, `skills-auto` 76,300 (−19%), `subagents` 528,200 (2 tác vụ; baseline trên cùng 2 tác vụ là 113,533, tức **gấp 4,7 lần**).
   - Điểm trên 100k token (tác vụ đánh giá): baseline 0.64; `skills-auto` 0.68; `subagents` 0.10.
   - **Đa tác tử không đáng chi phí** trong thí nghiệm này: điểm bằng hoặc thấp hơn baseline ở cả 4 tác vụ hợp lệ, nhưng tốn từ 1,08 lần (code-learn) đến 9,7 lần (data-eval) token, vì chia việc không cung cấp thêm quy ước nào.
5. **Rò rỉ và quá khớp.**
   - **Rò rỉ:** không có. `validate_skill` đã chặn hai lần một skill chứa từ trùng với định danh của tác vụ đánh giá (`orders`); thực chất đó là từ thông dụng, nên đây là dương tính giả. Curator chỉ đọc kết quả có `role == "learn"` (có test kiểm tra). Mình không mở `check.py`, và chỉ đọc vết của tác vụ đánh giá sau khi tạo tag `freeze`.
   - **Quá khớp nhẹ:** skill logs nêu cú pháp dòng lặp `-- last message repeated N times --` lấy từ log học. Trên logs-eval điều này không gây hại (các check kỹ thuật đạt).
6. **Nhiễu.**
   - Không chạy Phần 3.4 trước đóng băng (để dành hạn mức API cho lần chạy chính thức), nên **không có cặp đo nhiễu trực tiếp** cho cùng bộ skill.
   - Bằng chứng gián tiếp: (a) model bỏ qua `temperature=0`; (b) một lần chạy suy biến hoàn toàn (code-eval 1/11) dù tác tử đã đọc đúng skill; (c) `baseline/code-eval` chạy 2 lần (lần đầu gặp lỗi mạng giữa chừng) đều ra 7/11, cho thấy ở tác vụ này kết quả khá ổn định; (d) một check kỹ thuật đổi kết quả giữa các điều kiện mà không có lý do rõ (`low_stock_follows_docstring`).
   - Như vậy chênh lệch nhỏ hơn hoặc bằng 1 check mỗi tác vụ trong bảng không đáng tin. Chỉ các chênh lệch lớn, nhất quán và có cơ chế giải thích trong vết (tăng 3 check `rule_` ở code-learn, logs-learn, logs-eval) mới đủ để rút kết luận.

## 9. Hạn chế và tính hợp lệ

1. **Mỗi cấu hình chỉ chạy một lần, và model có nhiễu** (`temperature` bị bỏ qua, có một lần chạy suy biến). Một lần chạy hỏng làm đảo ngược kết luận trung bình trên tác vụ đánh giá (0.52 so với 0.60). Mọi chênh lệch nhỏ hơn hoặc bằng 1 check đều có thể là nhiễu. Cần ít nhất 3 lần lặp mỗi cấu hình để kết luận.
2. **Ít tác vụ** (3 học, 3 đánh giá, mỗi họ chỉ 1 cặp). Kết quả "skill giúp" thực chất dựa vào 2 họ (code, logs); họ data không có skill. Không thể khái quát cho loại tác vụ khác.
3. **Thiếu dữ liệu do hạ tầng và thời gian:** `subagents/data-learn` lỗi mạng; `subagents/logs-eval` bị ngắt nên không có kết quả. Kết luận về đa tác tử dựa trên 4 tác vụ (2 học, 2 đánh giá), nên trung bình cột `subagents` không so trực tiếp được với hai cột còn lại.
4. **Quy ước do giảng viên thiết kế** và được phát biểu chính xác trong `detail`. Curator chỉ cần chép lại, nên đây là trường hợp thuận lợi cho tiến hóa từ phản hồi. Trong thực tế, phản hồi thường mơ hồ hơn, và lần chạy curator đầu tiên (skill mơ hồ) cho thấy chất lượng skill phụ thuộc mạnh vào prompt của curator.
5. **Chỉ một model** (`gemini-3.5-flash-lite`, model nhỏ). Model mạnh hơn có thể tự suy ra một phần quy ước, hoặc tận dụng subagent tốt hơn.

## 10. Kết luận

Skill do curator tự sinh cải thiện rõ các check quy ước đã học: tác vụ học 0/9 → 6/9, và chuyển được sang logs-eval (6 → 9/10). Skill không giúp quy ước mới của tác vụ đánh giá, và không giúp họ data (skill bị bộ lọc rò rỉ chặn). Điểm trung bình trên tác vụ đánh giá không cho thấy cải thiện (0.52 so với 0.60), chủ yếu do một lần chạy suy biến; với một lần chạy mỗi cấu hình, không thể khẳng định hiệu quả tổng thể. Đa tác tử không tăng điểm ở tác vụ nào nhưng tốn 1,1–9,7 lần token, vì lỗi chủ yếu là thiếu quy ước chứ không phải thiếu năng lực xử lý. Đề xuất tiếp theo: lặp mỗi cấu hình ít nhất 3 lần để đo nhiễu, và thay bộ lọc rò rỉ dạng so khớp chuỗi bằng danh sách định danh chính xác (tên tệp, id) để không chặn nhầm từ thông dụng như "orders".

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
  9. (Ngày hạn mức được cấp lại) `python -m lab.runner --condition subagents --tasks data-learn logs-learn` → data-learn lỗi `RemoteProtocolError`, logs-learn 6/9.
  10. `python -m lab.curator` ×3 (lần 2 sau khi sửa prompt; lần 3 ghi ra `results/curator-run3/`), xem mục 6.
  11. `git commit -m "hypotheses"` (`0000d67`) → `git commit --allow-empty -m "freeze skills" && git tag freeze` (`8954721`).
  12. `python -m lab.runner --condition baseline --tasks eval`; `python -m lab.runner --condition skills-auto --tasks all`.
  13. `python scripts/verify_freeze.py` → OK; `python -m lab.compare > report/table.md`; `python scripts/check_breakdown.py`.
  14. `python -m lab.runner --condition baseline --tasks code-eval` (chạy lại sau lỗi mạng) → 7/11.
  15. `python -m lab.runner --condition subagents --tasks eval` → code-eval 7/11, data-eval 4/9; logs-eval bị ngắt (Ctrl+C).
  16. `python -m lab.compare > report/table.md`; `python scripts/check_breakdown.py`.
- Thử thách mở rộng (nếu có): không làm.
- Ghi chú khác:
  - **CRLF:** git trên Windows (`core.autocrlf=true`) đổi các tệp tác vụ sang CRLF khi checkout. Kiểm chứng bằng `grade()`: workspace `code-learn` chưa sửa đạt `tests_not_modified` ở dạng LF nhưng fail ở dạng CRLF. Mọi lần chạy trước khi sửa bị loại khỏi phân tích.
  - **Hạn mức API:** gói miễn phí của Gemini giới hạn 500 request/ngày/model; một lần chạy dùng khoảng 40–60 request (`subagents` nhiều hơn). Lỗi 429 là lỗi hạ tầng, không tính là lỗi tác tử; các lần chạy đó được chạy lại.
  - **Nhiệt độ:** `gemini-3.5-flash-lite` bỏ qua `temperature=0`, nên kết quả có nhiễu giữa các lần chạy.
