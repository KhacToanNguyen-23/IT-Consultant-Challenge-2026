"""Fills AI JOURNAL TEMPLATE.docx (blank) with the team's text. Anything wrapped in {{ }} is highlighted yellow = still missing.

    python docs/ai-journal/build_ai_journal.py      ->  docs/ai-journal/AI Journal.docx
Then open it in Word, replace the yellow parts, remove the highlight, File > Save As > PDF (AI Journal.pdf).
"""
import copy
import re
from pathlib import Path

import docx
from docx.enum.text import WD_COLOR_INDEX
from docx.oxml.ns import qn
from docx.shared import Inches, Pt

ROOT = Path(__file__).resolve().parents[2]
TEMPLATE = ROOT / "AI JOURNAL TEMPLATE.docx"
OUT = Path(__file__).resolve().parent / "AI Journal.docx"

TEAM = "orangeCore"
TOOLS = ("Claude agents (Claude Code) as the commanding agent for brainstorming, planning and review; Codex as the coding agent; "
         "Orca as the multi-agent workspace; a repository harness of skills (brainstorm, spec, plan, cook, fix, code-review) for the "
         "plan, build and test loop; Canva and Codex for the team's draft flow diagrams; Claude for the two submitted diagrams.")

STRATEGY = ("We ran a two-agent setup in Orca: Claude as the commanding agent and Codex as the coding agent. Claude brainstormed with us and "
            "asked questions until we closed the problem, then wrote a plan; Codex implemented it phase by phase. A phase moved on only when "
            "its tests passed, and we accepted the screens ourselves. Tests ran through a repository harness of skills (brainstorm, plan, "
            "cook, fix, code-review) that reports progress and asks before continuing. We rejected AI work that was technically fine but "
            "wrong for the business. In the product, AI is deliberately narrow: local embeddings suggest products, hard rules decide what is "
            "allowed, an optional LLM only helps read unusual wording, and a person confirms every order.")

USAGE = [
    ("Brainstorm and plan",
     "Claude as a thinking partner: it asked questions until we closed the problem, then produced the SRS and phase plans. Easy on a clear problem, harder on a vague one.",
     "~2 days", "~1 day",
     "We alone decided when a brainstorm was closed and what to build or drop. We cut stock reservations, a warehouse screen and a scheduler, and rewrote the “Zero PII” claim.",
     "SRS v2 and phase plans that Codex built against"),
    ("Build",
     "Codex built the plan phase by phase (counter review screen, e-mail quote flow, simulated POS connector with CSV fallback); the technology was settled quickly.",
     "~2 weeks for two developers (not feasible in the time available)", "~5 days",
     "A phase moved on only when its tests passed, and we accepted every screen ourselves. We rejected work that was technically fine but wrong for the business (see Reflection). AI bugs we caught: a phone mask that leaked digits, “15 stk … 4.8m” read as 4.8 m, and an e-mail order that could be confirmed without a quote.",
     "Both journeys work; a POS failure exports a CSV with the same reference"),
    ("Test and review",
     "Agents wrote and ran unit tests, API tests and UI checks through the harness; manual testing alone was slow and not accurate enough.",
     "~2 days (manual)", "~0.5 day",
     "244 backend tests and 33 live acceptance checks had to pass before the next phase; we accepted the UI by hand.",
     "Regressions found before the demo"),
    ("AI matching",
     "Local embeddings (e5-small, pgvector top-10) plus must-match rules, score bands and a rules fallback: handles many wording variants where pure rules are rigid, with staff confirming.",
     "~2 days", "~0.5 day",
     "Tests: C18 never matched as C24, 0.90 boundary, gap cap, substitutes never lower grade; AI-off toggle tested.",
     "Initial results on 98 lines: top-1 100% on answerable lines, 0 of 63 high-band lines wrong, 0 traps offered; 20-line analysis about 0.2 s locally"),
    ("Evaluation",
     "Several agents drafted 98 labelled lines (DA/NO/SV/EN, traps, missing attributes) and a report script, replacing a subjective judgement.",
     "~1 day", "~2 h + review",
     "A teammate reviewed {{[N] of 98 labels and corrected [M]}}. One rule gap found by the set (E046) was fixed, so the set is no longer fully independent.",
     "Report says “initial results”; the ≤2% high-band error target is not claimed"),
]

DECISIONS = [
    ("SKU matching design",
     "Let an LLM re-rank or pick the final SKU from the candidates.",
     "The LLM may not choose or re-rank a SKU. It stays an optional helper that reads unusual wording from masked text. Embeddings retrieve candidates, deterministic must-match rules remove unsafe ones (a C18 is never offered for C24), and unclear lines go to the associate, so the AI is never silently wrong."),
    ("Privacy wording and masking",
     "Early drafts promised “Zero PII / sovereign AI”, and an AI-written regex masked phone numbers.",
     "We downgraded the claim to “e-mail and phone are regex-masked; names and addresses are not guaranteed”. Testing showed the regex leaked digits before a full stop and the parser read an e-mail signature name as an order line; we fixed both and added tests."),
    ("Approval rule for e-mail orders",
     "Treat an e-mail request like a counter order: confirm it directly and let substitutes be accepted at any time.",
     "We set a business rule: when the customer is not present, nothing is committed to the POS until the customer has approved. We checked the AI-built flow against that rule and found a path where an e-mail request could reach the POS without a saved quote or a recorded approval. We required both (with tests) and relabelled the substitute button “Record customer agreement” until pick-up."),
]

REFLECTION = {
    "Where did AI help your team the most?":
        "Two agents with clear roles let us move fast: Claude helped us think and plan, and Codex built each phase quickly, so technology choices were settled early and unit, API and UI tests were easy to apply. Work that would not have fitted in the available days did.",
    "What AI output did you reject or modify, and why?":
        "We rejected several outputs that worked technically but did not fit the business: LLM re-ranking of SKUs, an e-mail flow where the customer's acceptance came before their approval, AI-style match scores shown while the AI was off, edit tools left open on lines that needed no action, and a diagram step (printing an invoice) the MVP does not have. We also fixed AI bugs: a phone mask that leaked digits and a parser that read “15 stk … 4.8m” as 4.8 m.",
    "What engineering or business decisions required human judgment?":
        "We decided when each brainstorm was closed and accepted every phase ourselves. We also decided the scope (no stock reservations or scheduler), what the product may promise (a quote never reserves stock), that the customer and not the associate accepts a substitute, and that unclear lines are never guessed.",
    "Are there any obstacles when using AI?":
        "Turning a brainstorm into business rules was the hardest part: the rules we wrote down sometimes stopped matching how the counter really works (for example, when a substitute may be accepted in an e-mail order), and the agents followed them literally, so we had to revisit them as the product took shape. UI design is also hard to delegate: agents build screens quickly but cannot judge clarity, so the person directing them has to understand UI and review every screen. AI is also optimistic: it drafted the evaluation labels and scored itself 100%, so we added human review. With one commanding agent and one coding agent, conflicts were rare, and we have no automated browser tests yet.",
}


def add_runs(par, text, size=None, bold=False):
    """Text with {{...}} segments highlighted in yellow."""
    for part in re.split(r"(\{\{.*?\}\})", text):
        if not part:
            continue
        hl = part.startswith("{{")
        run = par.add_run(part[2:-2] if hl else part)
        run.bold = bold
        if size:
            run.font.size = Pt(size)
        if hl:
            run.font.highlight_color = WD_COLOR_INDEX.YELLOW


def set_cell(cell, text, size=8.5):
    par = cell.paragraphs[0]
    for r in list(par.runs):
        r._r.getparent().remove(r._r)
    add_runs(par, text, size=size)


def insert_after(par, text, size=None):
    new = copy.deepcopy(par._p)
    for child in list(new):
        if child.tag.endswith("}r") or child.tag.endswith("}hyperlink"):
            new.remove(child)
    par._p.addnext(new)
    from docx.text.paragraph import Paragraph

    p = Paragraph(new, par._parent)
    ppr = new.find("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}pPr")
    if ppr is not None:  # answers are plain paragraphs, not list items
        for tag in ("numPr",):
            el = ppr.find("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}" + tag)
            if el is not None:
                ppr.remove(el)
    p.style = par.part.document.styles["Normal"]
    add_runs(p, text, size=size)
    return p


def fill_sdt(tr, text):
    """The template's Team name / AI Tools cells are content controls wrapping the cell: replace the placeholder."""
    from docx.oxml.ns import qn
    from docx.text.paragraph import Paragraph

    sdt = tr.find(qn("w:sdt"))
    pr = sdt.find(qn("w:sdtPr"))
    plc = pr.find(qn("w:showingPlcHdr"))
    if plc is not None:
        pr.remove(plc)
    p_el = sdt.find(qn("w:sdtContent")).find(qn("w:tc")).find(qn("w:p"))
    for r in p_el.findall(qn("w:r")):
        p_el.remove(r)
    add_runs(Paragraph(p_el, None), text)


def fill_block_sdt(sdt, text):
    """Block-level content control (the template's answer boxes): replace the placeholder text."""
    from docx.text.paragraph import Paragraph

    pr = sdt.find(qn("w:sdtPr"))
    plc = pr.find(qn("w:showingPlcHdr"))
    if plc is not None:
        pr.remove(plc)
    p_el = sdt.find(qn("w:sdtContent")).find(qn("w:p"))
    for r in p_el.findall(qn("w:r")):
        p_el.remove(r)
    add_runs(Paragraph(p_el, None), text)


def main():
    d = docx.Document(str(TEMPLATE))
    head, usage, decisions = d.tables[0], d.tables[1], d.tables[2]

    fill_sdt(head._tbl.tr_lst[0], TEAM)
    fill_sdt(head._tbl.tr_lst[1], TOOLS)

    assert len(STRATEGY.split()) <= 150, len(STRATEGY.split())
    blocks = [ch for ch in d.element.body.iterchildren() if ch.tag == qn("w:sdt")]
    assert len(blocks) == 5, len(blocks)  # strategy + the four reflection answers, in document order

    for i, row in enumerate(USAGE, start=1):
        for j, text in enumerate(row):
            set_cell(usage.rows[i].cells[j], text)
    for i, row in enumerate(DECISIONS, start=1):
        for j, text in enumerate(row):
            set_cell(decisions.rows[i].cells[j], text, size=9)

    for table, widths in ((usage, [0.75, 1.45, 0.75, 0.7, 1.75, 1.1]), (decisions, [1.2, 2.0, 3.3])):
        table.autofit = False
        for row in table.rows:
            for cell, w in zip(row.cells, widths):
                cell.width = Inches(w)

    answers = [STRATEGY] + list(REFLECTION.values())
    for block, text in zip(blocks, answers):
        fill_block_sdt(block, text)

    d.save(str(OUT))
    print("saved", OUT, "| strategy words:", len(STRATEGY.split()))


if __name__ == "__main__":
    main()
