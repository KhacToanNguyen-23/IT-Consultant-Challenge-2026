# AI Journal: bản nháp (đã cập nhật theo câu trả lời của nhóm)

Điền vào mẫu trống `AI JOURNAL TEMPLATE.docx`. Chỗ **[CONFIRM]** là việc nhóm cần xác nhận; không để lại ký hiệu này trong PDF.

## Team name và AI Tools used

**Team name:** orangeCore

**AI Tools used:** Claude agents (Claude Code) as the commanding agent for brainstorming, planning and review; Codex as the coding agent; Orca as the multi-agent workspace; a repository harness of skills (brainstorm, spec, plan, cook, fix, code-review) for the plan, build and test loop; Canva and Codex for the team's draft flow diagrams; Claude for the two submitted diagrams.

## AI Strategy (khoảng 130 từ, giới hạn 150)

> We ran a two-agent setup in Orca: Claude as the commanding agent and Codex as the coding agent. Claude brainstormed with us and asked questions until we closed the problem, then wrote a plan; Codex implemented it phase by phase. A phase moved on only when its tests passed, and we accepted the screens ourselves. Tests ran through a repository harness of skills (brainstorm, plan, cook, fix, code-review) that reports progress and asks before continuing. We rejected AI work that was technically fine but wrong for the business. In the product, AI is deliberately narrow: local embeddings suggest products, hard rules decide what is allowed, an optional LLM only helps read unusual wording, and a person confirms every order.

## AI Usage log (5 dòng)

Thời gian là **đề xuất**, nhóm sửa nếu lệch: [CONFIRM].

| Stage | Purpose of using AI | Original time estimate | Actual time with AI | Human Validation | Outcome |
|---|---|---|---|---|---|
| Brainstorm and plan | Claude as a thinking partner: it asked questions until we closed the problem, then produced the SRS and phase plans. Easy on a clear problem, harder on a vague one. | [~2 days] | [~1 day] | We alone decided when a brainstorm was closed and what to build or drop; we cut stock reservations, a warehouse screen and a scheduler, and rewrote the "Zero PII" claim | SRS v2 and phase plans that Codex built against |
| Build | Codex built the plan phase by phase (counter review screen, e-mail quote flow, simulated POS connector with CSV fallback); the technology was settled quickly | [~2 weeks for two developers, not feasible in the time available] | [~5 days] | A phase moved on only when its tests passed; we accepted every screen ourselves; we rejected work that was technically fine but wrong for the business (see Reflection); AI bugs we caught: a phone mask that leaked digits, "15 stk … 4.8m" read as 4.8 m, an e-mail order that could be confirmed without a quote | Both journeys work; a POS failure exports a CSV with the same reference |
| Test and review | Agents wrote and ran unit tests, API tests and UI checks through the harness; manual testing alone was slow and not accurate enough | [~2 days manual] | [~0.5 day] | 244 backend tests and 33 live acceptance checks had to pass before the next phase; we accepted the UI by hand | Regressions found before the demo |
| AI matching | Local embeddings (e5-small, pgvector top-10) plus must-match rules, score bands and a rules fallback: handles many wording variants where pure rules are rigid, with staff confirming | [~2 days] | [~0.5 day] | Tests: C18 never matched as C24, 0.90 boundary, gap cap, substitutes never lower grade; AI-off toggle tested | Initial results on 98 lines: top-1 100% on answerable lines, 0 of 63 high-band lines wrong, 0 traps offered; 20-line analysis about 0.2 s locally |
| Evaluation | Several agents drafted 98 labelled lines (DA/NO/SV/EN, traps, missing attributes) and a report script, replacing a subjective judgement | [~1 day] | [~2 h + review] | A teammate reviewed the labels: [CONFIRM N/98 reviewed, M corrected]. One rule gap found by the set (E046) was fixed, so the set is no longer fully independent | Report says "initial results"; the ≤2% high-band error target is not claimed |

## Key AI Decisions (3 ví dụ)

| Task | AI suggestion | What your team did |
|---|---|---|
| SKU matching design | Let an LLM re-rank or pick the final SKU from the candidates. | The LLM may not choose or re-rank a SKU. It stays an optional helper that reads unusual wording from masked text. Embeddings retrieve candidates, deterministic must-match rules remove unsafe ones (a C18 is never offered for C24), and unclear lines go to the associate, so the AI is never silently wrong. |
| Privacy wording and masking | Early drafts promised "Zero PII / sovereign AI", and an AI-written regex masked phone numbers. | We downgraded the claim to "e-mail and phone are regex-masked; names and addresses are not guaranteed". Testing showed the regex leaked digits before a full stop and the parser read an e-mail signature name as an order line; we fixed both and added tests. |
| Approval rule for e-mail orders | Treat an e-mail request like a counter order: confirm it directly and let substitutes be accepted at any time. | We set a business rule: when the customer is not present, nothing is committed to the POS until the customer has approved. We checked the AI-built flow against that rule and found a path where an e-mail request could reach the POS without a saved quote or a recorded approval. We required both (with tests) and relabelled the substitute button "Record customer agreement" until pick-up. |

## Reflection

**Where did AI help your team the most?**
Two agents with clear roles let us move fast: Claude helped us think and plan, and Codex built each phase quickly, so technology choices were settled early and unit, API and UI tests were easy to apply. Work that would not have fitted in the available days did.

**What AI output did you reject or modify, and why?**
We rejected several outputs that worked technically but did not fit the business: LLM re-ranking of SKUs, an e-mail flow where the customer's acceptance came before their approval, AI-style match scores shown while the AI was off, edit tools left open on lines that needed no action, and a diagram step (printing an invoice) the MVP does not have. We also fixed AI bugs: a phone mask that leaked digits and a parser that read "15 stk … 4.8m" as 4.8 m.

**What engineering or business decisions required human judgment?**
We decided when each brainstorm was closed and accepted every phase ourselves. We also decided the scope (no stock reservations or scheduler), what the product may promise (a quote never reserves stock), that the customer and not the associate accepts a substitute, and that unclear lines are never guessed.

**Are there any obstacles when using AI?**
Turning a brainstorm into business rules was the hardest part: the rules we wrote down sometimes stopped matching how the counter really works (for example, when a substitute may be accepted in an e-mail order), and the agents followed them literally, so we had to revisit them as the product took shape. UI design is also hard to delegate: agents build screens quickly but cannot judge clarity, so the person directing them has to understand UI and review every screen. AI is also optimistic: it drafted the evaluation labels and scored itself 100%, so we added human review. With one commanding agent and one coding agent, conflicts were rare, and we have no automated browser tests yet.

---

## Cần nhóm xác nhận trước khi xuất PDF

1. Các con số thời gian trong bảng Usage log (đề xuất ở trên).
2. N/98 nhãn đã duyệt và M dòng đã sửa (sau bước duyệt nhãn).
3. LLM bật hay tắt khi quay video (ảnh hưởng đến hai sơ đồ, hiện ghi "disabled in this demo").
4. Mọi chữ trong bản nháp đúng với việc nhóm đã làm; sửa lại giọng văn cho giống lời của nhóm.

Sau đó mình điền vào `AI JOURNAL TEMPLATE.docx` và xuất `AI Journal.pdf` bằng Word.
