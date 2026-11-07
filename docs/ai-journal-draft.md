# AI Journal: bản nháp từ phần 3 trở đi (dán vào mẫu trống `AI JOURNAL TEMPLATE.docx`)

Khung của bạn đã chốt: **AI Tools used** (Claude agents, Codex, Orca, bộ harness `bb-*`) và **ba vai của AI** (đối tác brainstorm và lập kế hoạch, người thực thi và gợi ý, người kiểm chứng).
Chỗ **[CONFIRM]** là sự thật chỉ bạn biết: sửa hoặc xóa trước khi nộp. Không để lại ký hiệu `[CONFIRM]` nào trong PDF.

## Team name và AI Tools used

**Team name:** [CONFIRM]

**AI Tools used:** Claude agents (Claude Code) for brainstorming, planning and review; Codex for implementation; Orca as the multi-agent workspace; a repository harness of skills (brainstorm, spec, plan, cook, fix, code-review). [CONFIRM: ghi thêm "Claude with a Canva MCP connector to draft presentation slides" nếu slide đó nằm trong bài Round 2 hoặc video; ghi thêm tên công cụ giọng đọc (text-to-speech) nếu video dùng giọng AI.]

## AI Strategy (khoảng 120 từ, giới hạn 150)

> We worked with several AI agents in Orca, each with a role. Claude acted as a thinking partner: it asked questions until we agreed the problem, then wrote a plan. Codex implemented the plan phase by phase, and we checked every phase before the next one started. A repository harness (brainstorm, spec, plan, cook, fix and code-review skills) kept this loop repeatable, and its hooks blocked sensitive files. Verification was layered: unit and contract tests, live acceptance runs, code review and a labelled evaluation set. Inside the product, AI is deliberately narrow: local embeddings suggest products, hard rules decide what is allowed, and a person confirms every order. We kept a record of what we rejected or changed.

## AI Usage log (5 dòng)

| Stage | Purpose of using AI | Original time estimate | Actual time with AI | Human Validation | Outcome |
|---|---|---|---|---|---|
| Brainstorm and plan | Claude questioned us until the problem and scope were agreed, then produced the SRS and phase plans | [CONFIRM] | [CONFIRM] | We closed each brainstorm ourselves and reviewed every requirement; we cut stock reservations, a warehouse screen and a scheduler, and rewrote the "Zero PII" claim | SRS v2 and phase plans that Codex built against |
| Build | Codex implemented the plan phase by phase: counter review screen, e-mail quote flow, simulated POS connector with CSV fallback | [CONFIRM] | [CONFIRM] | We checked every phase before the next one. We caught AI bugs: a phone mask that leaked digits, "15 stk … 4.8m" read as 4.8 m instead of 15, and an e-mail order that could be confirmed without a quote | Both journeys work; a POS failure exports a CSV with the same reference |
| Test and review | Agents ran unit tests, live acceptance checks and code review through the harness | [CONFIRM] | [CONFIRM] | 244 backend tests and 33 live acceptance checks; failures went back to a fix step; [CONFIRM: no phase accepted with open critical issues] | Regressions caught before the demo; one command re-checks the system |
| AI matching | Local embeddings (e5-small, pgvector top-10) plus must-match rules, score bands, ambiguity cap and a rules fallback | [CONFIRM] | [CONFIRM] | Tests: C18 never matched as C24, 0.90 boundary, gap cap, substitutes never lower grade; AI-off toggle tested | Initial results on 98 lines: top-1 100% on answerable lines, 0 of 63 high-band lines wrong, 0 traps offered; 20-line analysis about 0.2 s locally |
| Evaluation | AI drafted 98 labelled lines (DA/NO/SV/EN, traps, missing attributes) and a report script | [CONFIRM] | [CONFIRM] | A teammate reviewed the labels: [CONFIRM N/98 reviewed, M corrected]. One rule gap found by the set (E046) was fixed, so the set is no longer fully independent | Report says "initial results"; the ≤2% high-band error target is not claimed |

## Key AI Decisions (3 ví dụ)

| Task | AI suggestion | What your team did |
|---|---|---|
| SKU matching design | Let an LLM re-rank or pick the final SKU from the candidates. | Kept the LLM out of the decision path. Embeddings only retrieve candidates, deterministic must-match rules remove unsafe ones (a C18 is never offered for C24), and unclear lines go to the associate, so the AI is never silently wrong. |
| Privacy wording and masking | Early drafts promised "Zero PII / sovereign AI", and an AI-written regex masked phone numbers. | We downgraded the claim to "e-mail and phone are regex-masked; names and addresses are not guaranteed". Testing showed the regex leaked digits before a full stop and the parser read an e-mail signature name as an order line; we fixed both and added tests. |
| E-mail confirm path | Confirm an e-mail request like a counter order and let substitutes be accepted at any time. | [CONFIRM] A team question ("what if the customer never approves?") made us test every path. An e-mail session without a quote could still reach the POS, so we added a QUOTE_REQUIRED gate with tests, and the screen now says "Record customer agreement" until pick-up. |

## Reflection

**Where did AI help your team the most?**
Splitting the work between agents let us move from a brief to a tested spec and then to working code, tests, seed data and diagrams in days instead of weeks. It also produced edge cases we would not have written ourselves: Danish slang, Norwegian and Swedish wording, and lines that must not be guessed.

**What AI output did you reject or modify, and why?**
We rejected LLM re-ranking because a wrong grade is costly and the output is not repeatable. We rewrote "Zero PII / sovereign AI" to what we can prove, and fixed an AI-written phone mask that leaked digits, a parser that read "15 stk … 4.8m" as 4.8 m, and a screen that showed AI-style match scores while the AI was off.

**What engineering or business decisions required human judgment?**
We decided the scope (no stock reservations or scheduler), what the product may promise (a quote never reserves stock), that the customer and not the associate accepts a substitute, and that unclear lines are never guessed. We also decided to report results honestly: "initial results", simulated data and no claim on the 2% target.

**Are there any obstacles when using AI?**
AI is optimistic: it drafted the evaluation labels and then scored itself 100%, so we added human review. Several agents edited the same files in parallel, which caused overlapping changes until we agreed who owned which part [CONFIRM]. We also have no automated browser tests yet, so UI checks were manual.

---

## Về Canva và MCP: có cần khai không

- **Nguyên tắc:** khai mọi công cụ AI đã dùng cho **sản phẩm nộp ở Round 2** (video, hai sơ đồ, mã nguồn, AI Journal). Đề dùng AI Journal để hiểu cách nhóm dùng AI; khai đủ và trung thực không bị trừ điểm (chủ đề cuộc thi cho phép dùng AI).
- **Slide làm bằng Claude cộng MCP Canva:** nếu slide đó **không** nằm trong bài nộp Round 2 và không xuất hiện trong video (ví dụ chỉ là slide Round 1) thì không bắt buộc, nhưng ghi một cụm ngắn trong ô "AI Tools used" cũng không hại. Nếu **có dùng** (ví dụ thẻ chữ trong video làm từ slide đó) thì **nên khai**.
- Không cần mô tả kỹ thuật MCP. Một cụm như "Claude with a Canva MCP connector to draft slides" là đủ.
- Hai sơ đồ nộp hiện do công cụ viết mã và Chromium sinh ra, kèm luồng do thành viên vẽ bằng draw.io. Hãy ghi đúng nguồn: [CONFIRM: thành viên vẽ draw.io có dùng AI không].

## Bước tiếp theo

1. Bạn sửa các chỗ **[CONFIRM]** và đọc lại giọng văn cho giống lời của nhóm.
2. Gửi mình bản đã sửa: mình đối chiếu từng con số với kho mã, soát tiếng Anh.
3. Máy bạn có **Microsoft Word**, nên mình có thể điền vào `AI JOURNAL TEMPLATE.docx` và xuất `AI Journal.pdf` ngay khi nội dung chốt (hoặc bạn tự Save As PDF).
