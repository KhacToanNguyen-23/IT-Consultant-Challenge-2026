# Hướng dẫn hoàn thành các tài liệu còn thiếu (ngoài video)

Thứ tự làm: **B (duyệt nhãn) → A (AI Journal) → D (gửi bài)**. Mục C giải thích vì sao tắt LLM khi quay.
Chỗ đánh dấu **[CONFIRM]** là sự thật chỉ nhóm biết (thời gian, người làm, công cụ). Mình không bịa các chỗ này: bạn điền hoặc xác nhận.

---

## A. AI Journal (file `AI_Journal.docx` → xuất PDF)

Mẫu đề cho gồm: tên đội, công cụ AI, **AI Strategy (tối đa 150 từ)**, **AI Usage log (tối đa 5 việc)**, **Key AI Decisions (2–3 ví dụ)**, **Reflection (4 câu, mỗi câu 2–4 câu trả lời)**. Ngôn ngữ: tiếng Anh. File hiện đã có sẵn bảng Usage log và Key Decisions do AI soạn nháp; cần **cập nhật số liệu cũ**, điền các ô trống và xác nhận các `[TEAM: confirm]`.

### Số liệu cũ trong file cần sửa

| Trong file hiện tại | Sửa thành |
|---|---|
| "35 unit tests" | "244 automated backend tests and 33 live acceptance checks" |
| "top-1 99%", "20-line analyze p95 724 ms" | "top-1 100% on answerable lines", "p95 about 0.2 s (20 lines, local)" |
| "no tuning on this set" | Không còn đúng: dòng E046 từng sai và đã được sửa bằng cách thêm cụm từ. Ghi: "one rule gap found by the set (E046) was fixed, so the set is no longer fully independent" |
| Thiếu ví dụ lỗi AI mới | Thêm: parser đọc "15 stk … 4.8m" thành 4.8 m; đơn email gửi được khi chưa có báo giá |

### Các ô cần điền (bản nháp dán được)

**Team name:** **[CONFIRM tên đội]**

**AI Tools used:** Claude Code (Claude Pro), Codex (ChatGPT Plus). **[CONFIRM: có dùng công cụ giọng đọc (text-to-speech) cho video không, ghi tên nếu có]**

**AI Strategy (khoảng 125 từ):**
> We used AI as a pair of engineers working under our direction, not as an oracle. Claude Code and Codex wrote most of the code from a requirements spec (SRS) that AI helped draft and that we then cut and corrected. Inside the product, AI has a narrow role: a local embedding model retrieves candidate products, deterministic rules decide what is allowed, and a human confirms every order. An external LLM is optional and kept out of the decision path. We validated AI output with unit and contract tests, live acceptance runs, browser walk-throughs and a labelled evaluation set, and we recorded what we rejected or changed: an LLM re-ranker, an over-promising privacy claim, an unsafe e-mail confirm path, and AI-style confidence scores shown while the AI was off.

**AI Usage log (5 việc, điền từng cột; `[CONFIRM]` là thời gian của nhóm):**

| Stage | Purpose of using AI | Original time estimate | Actual time with AI | Human Validation | Outcome |
|---|---|---|---|---|---|
| Planning | Turn the Round 1 slides and the Round 2 brief into an MVP SRS (requirements, API contracts, plan, cut rules) | [CONFIRM ~3 days] | [CONFIRM ~1 day] | Team reviewed every requirement; removed reservations, warehouse UI and scheduler; rewrote the "Zero PII" claim | SRS v2, the scope-cut baseline all coders built against |
| Build | Implement the counter review UI, the e-mail quote flow and the simulated POS connector with CSV fallback (Claude Code, Codex) | [CONFIRM ~4 dev-days] | [CONFIRM ~1 day incl. review] | 244 backend tests, 33 live acceptance checks, browser walk-through of every demo case. Found and fixed AI bugs: phone mask leaking digits; "15 stk … 4.8m" ordering 4.8 m instead of 15; an e-mail order that could be confirmed without a quote | Both journeys work; a POS failure exports a CSV with the same reference |
| Data | Generate a deterministic 62-SKU catalog, stock, customers and a seed validator | [CONFIRM ~1 day] | [CONFIRM ~2 h] | Validator enforces groups and stock-out cases; [CONFIRM: a teammate spot-checked names and prices] | Repeatable seed; all prices and stock labelled simulated |
| AI matching | Local embeddings (e5-small, pgvector top-10) plus must-match rules, score bands, ambiguity cap and rules fallback | [CONFIRM ~2 days] | [CONFIRM ~0.5 day] | Tests: C18 never matched as C24, 0.90 boundary, gap cap, substitutes never lower grade; AI-off toggle tested | Initial results on 98 lines: top-1 100% on answerable lines, 0 of 63 high-band lines wrong, 0 traps offered; 20-line analysis p95 about 0.2 s locally; rules-only fallback close behind |
| Evaluation | Draft 98 labelled lines (DA/NO/SV/EN, traps, missing attributes) and a report script | [CONFIRM ~1 day] | [CONFIRM ~2 h + review] | Labels drafted by AI, then reviewed by a teammate: **[CONFIRM N/98 reviewed, M corrected, từ bước B]**. One rule gap found by the set (E046) was fixed, so the set is no longer fully independent | Report says "initial results"; the ≤2% high-band error target is not claimed |

**Key AI Decisions (chọn 3 trong 4 ví dụ dưới đây; mỗi ví dụ 3 cột Task / AI suggestion / What your team did):**

1. **SKU matching design.** AI suggestion: let an LLM re-rank or pick the final SKU. What we did: kept the LLM out of the decision path. Embeddings only retrieve candidates, deterministic must-match rules remove unsafe ones (a C18 is never offered for C24), and unclear lines go to the associate, so the AI is never silently wrong.
2. **Privacy wording and masking.** AI suggestion: early drafts promised "Zero PII / sovereign AI", and an AI-written regex masked phone numbers. What we did: downgraded the claim to "e-mail and phone are regex-masked; names and addresses are not guaranteed". Testing showed the regex leaked digits before a full stop, and the parser read an e-mail signature name as an order line; we fixed both and added tests.
3. **E-mail confirm path** (khuyên chọn, vì cho thấy kiểm chứng của con người). AI suggestion: confirm an e-mail request like a counter order and let substitutes be accepted at any time. What we did: a team question ("what if the customer never approves?") made us test every path; an e-mail session without a quote could still reach the POS. We added a QUOTE_REQUIRED gate and tests, and the screen now says "Record customer agreement" until pick-up. **[CONFIRM: đúng là nhóm đã đặt câu hỏi này]**
4. **Scope of the e-mail flow** (có thể thay cho ví dụ 3). AI suggestion: stock reservations, a warehouse screen, a scheduler and quote versioning. What we did: rejected them for a 5-day build; the quote keeps a price and stock snapshot, a before-and-after diff on reopen and a "not reserved" disclaimer.

**Reflection (mỗi câu 2–4 câu; bản nháp):**

- *Where did AI help your team the most?* AI turned a brief into a testable spec and then into working code, tests, seed data and diagrams in days instead of weeks. It also produced edge cases we would not have written ourselves: Danish slang, Norwegian and Swedish wording, and lines that must not be guessed.
- *What AI output did you reject or modify, and why?* We rejected LLM re-ranking because a wrong grade is costly and the output is not repeatable. We rewrote "Zero PII / sovereign AI" to what we can prove, and fixed an AI-written phone mask that leaked digits, a parser that read "15 stk … 4.8m" as 4.8 m, and a screen that showed AI-style match scores while the AI was off.
- *What engineering or business decisions required human judgment?* Scope (no stock reservations or scheduler), what the product may promise (a quote never reserves stock), that the customer and not the associate accepts a substitute, and that unclear lines are never guessed. We also decided to report results honestly: "initial results", simulated data and no claim on the 2% target.
- *Are there any obstacles when using AI?* AI is optimistic: it drafted the evaluation labels and then scored itself 100%, so we added human review. Several AI tools edited the same files in parallel, which caused overlapping edits until we agreed who owned which part **[CONFIRM]**. We also have no automated browser tests yet, so UI checks were manual.

### Cách điền và xuất

1. Mở `AI_Journal.docx` bằng Word. Điền các ô trên, thay mọi `[TEAM: confirm]` và `[CONFIRM …]` bằng nội dung thật; xóa mọi dấu ngoặc nhắc nhở.
2. Giữ nguyên bố cục mẫu của đề. Đếm lại AI Strategy ≤150 từ.
3. **File → Save As → PDF**, đặt tên `AI Journal.pdf`.
4. Mở PDF kiểm tra: không còn chữ `[CONFIRM]`, không có key hay mật khẩu, không có ký tự lỗi.

---

## B. Duyệt nhãn đánh giá (cho cột "Human Validation")

Vì sao: 98 dòng mẫu có "đáp án đúng" do AI soạn, chưa ai kiểm (0/98). Duyệt xong mới nói được "N dòng đã người duyệt".

1. **Xuất bảng** (đã có sẵn `docs/label-review-sheet.csv`; muốn tạo lại: `cd backend` rồi `python -m scripts.label_review export`).
2. Mở file CSV bằng Excel hoặc Google Sheets. Mỗi dòng có: câu khách viết, SKU đáp án, **tên sản phẩm của đáp án**, có phải dòng "phải hỏi lại" không, ghi chú.
3. Với **mỗi dòng**, điền cột `verdict`:
   - **OK**: đáp án đúng (sản phẩm đáp án thật sự là cái khách muốn).
   - **FIX**: đáp án sai. Ghi SKU đúng vào cột `correct_skus` (nhiều SKU cách nhau bằng dấu phẩy), hoặc **NONE** nếu hệ thống **không được tự chọn** sản phẩm nào (dòng thiếu thông tin, ngoài catalog).
   - Để trống nếu chưa duyệt.
4. Ưu tiên nếu ít thời gian (15 phút, khoảng 40 dòng): các dòng `trap`, `missing`, `slang`, rồi các dòng điểm cao. Người duyệt nên **không phải AI** (bạn hoặc thành viên BA).
5. **Lưu dưới dạng CSV** (giữ định dạng UTF-8), rồi chạy `python -m scripts.label_review apply` trong thư mục `backend`. Script đánh dấu `reviewed = true`, sửa đáp án ở các dòng FIX và in tổng số dòng đã duyệt.
6. Chạy lại báo cáo: `python -m scripts.evaluate`. Báo cáo mới ghi "labels human-reviewed: N/98". Nếu đáp án bị sửa, kết quả có thể giảm so với 100%: đó là kết quả trung thực.
7. Ghi N và M (số dòng đã sửa) vào ô Human Validation của dòng "Evaluation" ở mục A.

**Không chạy `seeds/build_evaluation.py` sau khi đã duyệt:** nó sinh lại file và xóa mọi cờ `reviewed`.

---

## C. Vì sao tắt khóa LLM khi quay (tắt thì có sao)

- **AI chính của sản phẩm không dùng khóa này.** Khớp SKU chạy bằng **mô hình embedding cục bộ** (`multilingual-e5-small`) và luật cứng, không cần khóa hay mạng. Khóa `LLM_API_KEY` chỉ bật một **LLM tùy chọn** để làm rõ vài dòng khó hiểu.
- **Tắt khóa thì hệ thống vẫn chạy y nguyên.** Mọi case demo (quầy, email, AI lỗi, POS lỗi) chạy được khi LLM tắt. Điều duy nhất mất đi là thẻ "AI tried to clarify N line(s)" khi LLM có tham gia.
- **Lý do nên tắt:**
  1. **Lời hứa "dữ liệu không rời máy".** Khi LLM bật, văn bản đã che sẽ gửi tới nhà cung cấp bên ngoài (DeepSeek, không phải nhà cung cấp EU), trái với slide 7 của Round 1 nói AI đặt tại EU.
  2. **Thời gian ổn định:** có LLM thì một lần phân tích có thể mất khoảng 1,4 giây, không có thì khoảng 0,2 giây.
  3. **Kết quả lặp lại được**, không phụ thuộc mạng hay nhà cung cấp.
  4. **An toàn bí mật:** khóa hiện tại đã dán trong chat, nên coi như đã lộ; sau cuộc thi nên tạo khóa mới. Tuyệt đối không để khóa lọt vào khung hình hay file nộp.
- **Cách tắt:** mở `.env`, để trống `LLM_API_KEY=`, rồi `docker compose up -d backend`. Kiểm tra: `/api/health` hiện `"llm": ...` không còn hoạt động hoặc thẻ "AI tried to clarify" biến mất.

---

## D. Gửi bài

1. Bốn file: `MVP.mp4`, `User Journey.pdf`, `System Diagram.pdf`, `AI Journal.pdf`.
2. Email tới `EB.VN@netcompany.com`, tiêu đề **"Round 2 – tên đội"**, **trước 22:00 ngày 9/11 (GMT+7)**, nên gửi sớm vài giờ.
3. Mở từng file trên máy khác, đảm bảo không có key, mật khẩu hay thông tin bí mật, và tên file đúng.
