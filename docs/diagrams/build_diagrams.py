"""Generates the two Round 2 diagram documents as print-ready HTML (A4 landscape, 2 pages each).

    python docs/diagrams/build_diagrams.py     ->  System Diagram.html, User Journey.html
Export to PDF with Chromium (page.pdf, preferCSSPageSize). Fonts stay >= 11 px (about 8.5 pt) on A4.
"""
import html
import os
import textwrap

OUT = os.path.dirname(os.path.abspath(__file__))
W, H = 1123, 794
NAVY, BLUE, GREY, GREEN, AMBER = "#0b3a6b", "#1768ac", "#6b7280", "#2d8a5a", "#b45309"


def esc(s):
    return html.escape(s, quote=False)


def tx(x, y, lines, size=12, weight=400, fill="#1b2430", anchor="start", lh=None):
    lh = lh or size * 1.3
    if isinstance(lines, str):
        lines = [lines]
    out = [f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" fill="{fill}" text-anchor="{anchor}">']
    for i, ln in enumerate(lines):
        out.append(f'<tspan x="{x}" dy="{0 if i == 0 else lh}">{esc(ln)}</tspan>')
    out.append("</text>")
    return "".join(out)


def box(x, y, w, h, title, lines=(), fill=BLUE, stroke=None, dash=False, tcolor="#fff", tsize=14, lsize=12, r=10, sub=None):
    d = ' stroke-dasharray="7 5"' if dash else ""
    s = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}" stroke="{stroke or fill}" stroke-width="2"{d}/>'
    cy = y + 24
    s += tx(x + w / 2, cy, title, tsize, 700, tcolor, "middle")
    if sub:
        cy += 17
        s += tx(x + w / 2, cy, sub, 11, 400, tcolor, "middle")
    if lines:
        s += tx(x + w / 2, cy + 20, list(lines), lsize, 400, tcolor, "middle", lsize * 1.35)
    return s


def wrapped(text, n):
    return textwrap.wrap(text, n)


def label(x, y, lines, size=11.5, anchor="middle", bold=False):
    if isinstance(lines, str):
        lines = [lines]
    wd = max(len(l) for l in lines) * size * 0.56 + 10
    hh = len(lines) * size * 1.3 + 6
    x0 = x - wd / 2 if anchor == "middle" else x - 4
    s = f'<rect x="{x0}" y="{y - size - 1}" width="{wd}" height="{hh}" rx="4" fill="#fff" opacity="0.94"/>'
    s += tx(x, y, lines, size, 700 if bold else 500, "#243447", anchor, size * 1.3)
    return s


def arrow(pts, dash=False, color="#5b6b7e", width=2):
    d = "M" + " L".join(f"{x},{y}" for x, y in pts)
    da = ' stroke-dasharray="7 5"' if dash else ""
    return f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{width}"{da} marker-end="url(#ah)"/>'


def note(x, y, w, h, head, body, size=11.5):
    s = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="#fff8e1" stroke="#e0c35a"/>'
    s += tx(x + 12, y + 20, head, 12, 800, "#7a5a00")
    s += tx(x + 12, y + 38, body, size, 400, "#3b3320", "start", size * 1.32)
    return s


def page_svg(inner, title, subtitle, n, total, docname):
    defs = ('<defs><marker id="ah" markerUnits="userSpaceOnUse" markerWidth="11" markerHeight="9" refX="10" refY="4.5" orient="auto">'
            '<path d="M0,0 L11,4.5 L0,9 z" fill="#5b6b7e"/></marker></defs>')
    head = tx(40, 46, title, 24, 800, NAVY) + tx(40, 68, subtitle, 13, 400, "#52627a")
    foot = tx(40, H - 18, f"SiteDesk MVP · IT Consultant Challenge 2026 · Round 2 · POS, stock, prices and customers are simulated", 11, 400, "#7a8798")
    foot += tx(W - 40, H - 18, f"{docname} · page {n}/{total}", 11, 400, "#7a8798", "end")
    return (f'<section class="page"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
            f'font-family="Segoe UI, Arial, sans-serif">{defs}<rect width="{W}" height="{H}" fill="#ffffff"/>{head}{inner}{foot}</svg></section>')


def document(title, pages):
    css = ("@page{size:297mm 210mm;margin:0}*{box-sizing:border-box}body{margin:0;background:#fff}"
           ".page{width:297mm;height:210mm;overflow:hidden;page-break-after:always}.page:last-child{page-break-after:auto}"
           ".page svg{display:block;width:100%;height:100%}")
    return f"<!doctype html><html lang='en'><head><meta charset='utf-8'><title>{title}</title><style>{css}</style></head><body>{''.join(pages)}</body></html>"



def chip(x, y, color, text, stroke=None, dash=False, w=11):
    d = ' stroke-dasharray="3 2"' if dash else ""
    return f'<rect x="{x}" y="{y - 10}" width="{w}" height="{w}" rx="3" fill="{color}" stroke="{stroke or color}" stroke-width="1.5"{d}/>' + tx(x + w + 6, y, text, 11, 500, "#334155")


def legend_system():
    y = 757
    s = chip(40, y, NAVY, "Person") + chip(105, y, BLUE, "SiteDesk part") + chip(205, y, GREEN, "Data store") + chip(285, y, GREY, "External, simulated")
    s += chip(425, y, "#eef0f3", "External, optional or manual", stroke=GREY, dash=True)
    s += tx(1083, y, "FR = requirement in the team's SRS v2", 11, 500, "#334155", "end")
    return s


def legend_journey():
    y = 757
    s = chip(40, y, "#ede7fb", "AI-assisted (local embeddings)", stroke="#9b87d8", w=13)
    s += chip(300, y, "#dbe9f9", "Hard rules (deterministic)", stroke="#6f9ad0", w=13)
    s += chip(480, y, "#e8f4ec", "Human decision or action", stroke="#8fc3a0", w=13)
    s += chip(650, y, "#fde7c7", "R1 = Round 1 problem", stroke="#e8a64a", w=13)
    s += tx(1083, y, "FR = requirement in the team's SRS v2", 11, 500, "#334155", "end")
    return s


# ============================================================ SYSTEM DIAGRAM
def legend_dfd():
    y = 757
    out = f'<rect x="40" y="{y - 10}" width="12" height="12" fill="{NAVY}"/>' + tx(58, y, "External entity (square)", 11, 500, "#334155")
    out += f'<circle cx="236" cy="{y - 4}" r="7" fill="{BLUE}" stroke="{NAVY}" stroke-width="1.5"/>' + tx(249, y, "System (circle)", 11, 500, "#334155")
    out += f'<path d="M370,{y - 4} L398,{y - 4}" stroke="#5b6b7e" stroke-width="2" marker-end="url(#ah)"/>' + tx(408, y, "Data flow, named by the data it carries", 11, 500, "#334155")
    out += f'<path d="M640,{y - 4} L668,{y - 4}" stroke="#5b6b7e" stroke-width="2" stroke-dasharray="6 4" marker-end="url(#ah)"/>' + tx(678, y, "Optional or indirect flow", 11, 500, "#334155")
    out += tx(1083, y, "FR = requirement in the team's SRS v2", 11, 500, "#334155", "end")
    return out


def sys_page1():
    s = ""
    cx, cy, r = 561, 395, 135
    # system = one circle
    s += f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{BLUE}" stroke="{NAVY}" stroke-width="3"/>'
    s += tx(cx, cy - 62, "SiteDesk", 22, 800, "#fff", "middle")
    s += tx(cx, cy - 42, "process 0 · AI-assisted counter screen", 11, 400, "#dbeafe", "middle")
    s += tx(cx, cy - 12, ["Intake and masking  (FR-001, 002)", "Matching, hard rules  (FR-006 to 009)", "Conversion, stock, alternatives", "(FR-011 to 016)", "Quotes, order export, CSV", "(FR-018 to 028)"], 11.5, 500, "#fff", "middle", 15.5)
    # external entities = squares
    s += box(60, 330, 200, 160, "Counter associate", ["Person · uses SiteDesk", "reads, reviews,", "decides, confirms"], fill=NAVY, r=2, sub="External entity")
    s += box(461, 100, 200, 90, "Customer", ["Person · outside SiteDesk"], fill=NAVY, r=2, sub="External entity", lsize=11)
    s += box(880, 200, 200, 130, "LLM API provider", ["Optional, masked text only;", "on or off by configuration"], fill="#eef0f3", stroke=GREY, dash=True, tcolor="#374151", r=2, sub="External entity")
    s += box(880, 380, 200, 140, "mock-pos", ["Simulated POS/ERP:", "catalog, price, stock,", "customers, orders"], fill=GREY, r=2, sub="External entity · simulated")
    s += box(880, 560, 200, 90, "Legacy POS", ["Manual entry from the CSV"], fill="#eef0f3", stroke=GREY, dash=True, tcolor="#374151", r=2, sub="External entity · manual", lsize=11)
    # data flows
    s += arrow([(260, 375), (427, 375)])
    s += label(343, 355, ["List · edits", "decisions · Confirm"])
    s += arrow([(434, 440), (260, 440)])
    s += label(343, 462, ["Review table · options", "receipt · CSV · quote"])
    s += arrow([(520, 190), (520, 266)], dash=True)
    s += label(405, 222, ["List · agreement", "(via the associate)"])
    s += arrow([(602, 266), (602, 190)], dash=True)
    s += label(614, 222, ["Quote · pick slip · reply", "(via the associate)"], anchor="start")
    s += arrow([(623, 275), (880, 275)], dash=True)
    s += label(752, 262, ["Masked text only"])
    s += arrow([(880, 310), (666, 310)], dash=True)
    s += label(773, 333, ["Extracted attributes"])
    s += arrow([(694, 415), (880, 415)])
    s += label(787, 396, ["Order payload", "stock queries"])
    s += arrow([(880, 480), (666, 480)])
    s += label(773, 504, ["Catalog · price · stock", "POS reference or error"])
    s += arrow([(620, 516), (620, 605), (880, 605)], dash=True)
    s += label(750, 590, ["CSV order export", "(keyed in by hand)"])
    s += note(40, 660, 345, 74, "MVP SCOPE", ["Sign-in is simulated (not SSO). Embeddings run locally;", "the LLM is optional. Prices and stock come from mock-pos."])
    s += note(400, 660, 345, 74, "DATA LIMIT", ["A regex masks e-mail and phone before any AI call.", "Names and addresses in free text are not guaranteed removed."])
    s += note(760, 660, 345, 74, "OUTCOME", ["POS accepts: POS_ACCEPTED + reference. POS 503 or timeout:", "CSV and NEEDS_MANUAL; the POS has not accepted the order."])
    s += legend_dfd()
    return page_svg(s, "SiteDesk MVP: context diagram (system and data flows)", "The system as one process, the external entities around it, and the data that flows in and out. Container view on page 2. SRS v2 §3, §7.", 1, 2, "System Diagram")


def sys_page2():
    s = ""
    s += box(40, 175, 185, 100, "Counter associate", ["Uses the counter and", "quote screens"], fill=NAVY, sub="Person")
    s += '<rect x="280" y="108" width="570" height="486" rx="16" fill="#f1f6fc" stroke="#7aa6d6" stroke-width="2" stroke-dasharray="9 6"/>'
    s += tx(298, 132, "SiteDesk · containers", 13, 700, NAVY)
    s += box(305, 160, 180, 120, "Web UI", ["Intake, review by exception,", "quotes, print, demo toggles"], fill=BLUE, sub="Next.js 14", lsize=11)
    s += box(590, 150, 235, 330, "Core API", [
        "Parse + PII masking · FR-001/002", "Matcher + hard rules · FR-006 to 009", "Convert, stock, alternatives · FR-011 to 016",
        "Quotes, orders · FR-018 to 028"], fill=BLUE, sub="FastAPI (Python)", lsize=11)
    for i, (h, b1, b2) in enumerate([("Local AI pipeline", "multilingual-e5-small + hard rules", "no data leaves SiteDesk"),
                                      ("AI Gateway", "optional LLM adapter", "on or off by configuration"),
                                      ("Local Connector", "POS calls, order push", "CSV fallback (FR-019)")]):
        y0 = 296 + i * 59
        s += f'<rect x="604" y="{y0}" width="207" height="52" rx="8" fill="#e9f3ff" stroke="#9bc5e5" stroke-width="2"/>'
        s += tx(707, y0 + 18, h, 12, 700, NAVY, "middle") + tx(707, y0 + 32, b1, 11, 400, "#244a6e", "middle") + tx(707, y0 + 45, b2, 11, 400, "#244a6e", "middle")
    s += box(305, 340, 180, 160, "SiteDesk DB", ["Catalog + vectors,", "sessions, quotes,", "decisions, audit"], fill=GREEN, sub="PostgreSQL 15 + pgvector", lsize=11)
    s += box(920, 150, 185, 100, "LLM API", ["Optional; on or off", "by configuration"], fill="#eef0f3", stroke=GREY, dash=True, tcolor="#374151", sub="External · optional")
    s += box(920, 320, 185, 115, "mock-pos", ["Simulated catalog,", "stock, customers,", "order receipt"], fill=GREY, sub="External · simulated")
    s += arrow([(225, 225), (305, 225)])
    s += label(265, 203, ["Browser", "[HTTP]"])
    s += arrow([(485, 220), (590, 220)])
    s += label(537, 198, ["REST", "[JSON]"])
    s += arrow([(590, 420), (485, 420)])
    s += label(537, 404, ["SQL", "pgvector"])
    s += arrow([(825, 215), (920, 215)], dash=True)
    s += label(872, 193, ["Masked text", "[HTTPS]"])
    s += arrow([(825, 380), (920, 380)])
    s += label(872, 350, ["Catalog, stock,", "customers, orders"])
    s += label(872, 406, ["[REST / JSON]"])
    s += note(40, 625, 345, 100, "CONTAINER RULE", ["The AI Gateway and the Local Connector are in-process", "modules of the FastAPI core, not separate containers.", "The vector index lives inside PostgreSQL (pgvector)."])
    s += note(400, 625, 345, 100, "AI AND PRIVACY", ["Matching runs on local embeddings plus hard rules,", "so the AI path needs no external service.", "The LLM, when enabled, only sees masked text."])
    s += note(760, 625, 345, 100, "FALLBACK", ["POS 503 / timeout: the connector writes a CSV and", "the order is marked NEEDS_MANUAL, not POS_ACCEPTED.", "AI off: rules and manual catalog search continue."])
    s += legend_system()
    return page_svg(s, "SiteDesk MVP: inside the system (containers)", "What is inside the circle of page 1: deployable parts, the data store, and how they talk to each other and to the outside. Run locally with Docker Compose.", 2, 2, "System Diagram")


# ============================================================ USER JOURNEY (swimlane flowcharts)
NW, NH, DW, DH, EW, EH = 88, 64, 90, 76, 104, 70
PITCH, XB = 105, 100
LANEBOX = [("Customer", 92, 120), ("Counter associate", 212, 140), ("SiteDesk", 352, 230)]
ROWY = {"C": 152, "A": 282, "M": 432, "E": 532}
ROLE = {"human": ("#e8f4ec", "#8fc3a0"), "rules": ("#dbe9f9", "#6f9ad0"), "ai": ("#ede7fb", "#9b87d8"),
        "fallback": ("#fff1dc", "#e0a040"), "decision": ("#fff8e1", "#d9b44a"), "done": ("#d3eddc", "#2d8a5a")}
AMBER_LINE = "#c8741a"


def cx(col):
    return XB + col * PITCH


def gx(c1, c2):
    return (cx(c1) + cx(c2)) / 2


class Flow:
    def __init__(self):
        self.nodes, self.body = {}, ""

    def node(self, nid, col, row, text, role, fr=None, shape="box"):
        x, y = cx(col), ROWY[row]
        w, h = {"box": (NW, NH), "diamond": (DW, DH), "ellipse": (EW, EH)}[shape]
        self.nodes[nid] = (x, y, w, h)
        fill, stroke = ROLE[role]
        if shape == "box":
            self.body += f'<rect x="{x - w / 2}" y="{y - h / 2}" width="{w}" height="{h}" rx="8" fill="{fill}" stroke="{stroke}" stroke-width="1.8"/>'
        elif shape == "diamond":
            pts = f"{x},{y - h / 2} {x + w / 2},{y} {x},{y + h / 2} {x - w / 2},{y}"
            self.body += f'<polygon points="{pts}" fill="{fill}" stroke="{stroke}" stroke-width="1.8"/>'
        else:
            self.body += f'<ellipse cx="{x}" cy="{y}" rx="{w / 2}" ry="{h / 2}" fill="{fill}" stroke="{stroke}" stroke-width="2"/>'
        lines = wrapped(text, {"box": 14, "diamond": 10, "ellipse": 12}[shape])
        n = len(lines) + (1 if fr else 0)
        y0 = y - (n - 1) * 13 / 2 + 4
        self.body += tx(x, y0, lines, 11, 600, "#17202c", "middle", 13)
        if fr:
            self.body += tx(x, y0 + len(lines) * 13, fr, 10.7, 700, "#1f4f86", "middle")

    def p(self, nid, side, dx=0, dy=0):
        x, y, w, h = self.nodes[nid]
        return {"top": (x + dx, y - h / 2 + dy), "bottom": (x + dx, y + h / 2 + dy), "left": (x - w / 2 + dx, y + dy), "right": (x + w / 2 + dx, y + dy)}[side]

    def edge(self, pts, color="#5b6b7e", dash=False):
        self.body += arrow(pts, dash=dash, color=color)

    def tag(self, x, y, text, anchor="middle"):
        wd = len(text) * 6.2 + 8
        x0 = x - wd / 2 if anchor == "middle" else (x - wd + 2 if anchor == "end" else x - 2)
        self.body += f'<rect x="{x0}" y="{y - 11}" width="{wd}" height="15" rx="3" fill="#fff" opacity="0.92"/>' + tx(x, y, text, 11, 700, "#334155", anchor)


def lanes_svg():
    s = ""
    for i, (name, y, h) in enumerate(LANEBOX):
        s += f'<rect x="20" y="{y}" width="1085" height="{h}" fill="{"#f8fafd" if i % 2 == 0 else "#f1f5fb"}" stroke="#d3deec"/>'
        s += f'<rect x="20" y="{y}" width="30" height="{h}" fill="{NAVY}"/>'
        s += f'<text transform="translate(41,{y + h / 2}) rotate(-90)" font-size="12.5" font-weight="700" fill="#fff" text-anchor="middle">{esc(name)}</text>'
    return s


def r1_band2(spans):
    y, h = 596, 40
    s = f'<rect x="20" y="{y}" width="1085" height="{h}" fill="#fff8ec" stroke="#f0d3a0"/>'
    s += f'<rect x="20" y="{y}" width="30" height="{h}" fill="#e8a64a"/>' + tx(35, y + 25, "R1", 12, 800, "#fff", "middle")
    for c1, c2, text in spans:
        x1, x2 = cx(c1) - 46, cx(c2) + 46
        s += f'<rect x="{x1}" y="{y + 5}" width="{x2 - x1}" height="{h - 10}" rx="6" fill="#fde7c7" stroke="#e8a64a"/>'
        lines = wrapped(text, int((x2 - x1 - 12) / 5.8))[:2]
        s += tx((x1 + x2) / 2, y + 19 if len(lines) == 1 else y + 16, lines, 11, 600, "#7a4300", "middle", 11.5)
    return s


def back_half(f, first_resolve_col):
    """Shared tail: all lines resolved? -> pick client + Confirm -> POS accepts? -> reference, or CSV."""
    f.node("a6", 6, "A", "Picks client, then Confirm", "human", "FR-017-018")
    f.node("s7", 7, "M", "POS accepts?", "decision", shape="diamond")
    f.node("e7", 7, "E", "Writes CSV, manual entry", "fallback", "FR-019")
    f.node("a8", 8, "A", "Downloads CSV, keys it in", "fallback")
    f.node("s9", 9, "M", "POS_ACCEPTED + reference", "done", "FR-019", "ellipse")
    f.node("c9", 9, "C", "Receives the order reference", "human")
    x6, x7 = cx(6), cx(7)
    f.edge([f.p("s5", "right"), (x6, ROWY["M"]), (x6, f.p("a6", "bottom")[1])])
    f.tag(cx(5) + 34, 409, "Yes")
    f.edge([f.p("a6", "right"), (x7, ROWY["A"]), f.p("s7", "top")])
    f.edge([f.p("s7", "right"), f.p("s9", "left")])
    f.tag(cx(7) + 34, 409, "Yes")
    f.edge([f.p("s7", "bottom"), f.p("e7", "top")], color=AMBER_LINE)
    f.tag(x7 + 14, 490, "No", "start")
    f.edge([f.p("e7", "right"), (cx(8), ROWY["E"]), f.p("a8", "bottom")], color=AMBER_LINE)
    f.edge([f.p("s9", "top"), f.p("c9", "bottom")])


def resolve_loop(f, col_a, col_c, col_s):
    """Associate resolves lines with the customer; SiteDesk re-checks and the gate is evaluated again."""
    xa = cx(col_a)
    f.edge([f.p("a%d" % col_a, "top", -12), f.p("c%d" % col_c, "bottom", -12)])
    f.tag(xa - 18, 232, "asks", "end")
    f.edge([f.p("c%d" % col_c, "bottom", 12), f.p("a%d" % col_a, "top", 12)])
    f.tag(xa + 18, 232, "decides", "start")


def journey_page(title, subtitle, f, spans, note_text, page_no):
    s = lanes_svg() + f.body + r1_band2(spans)
    s += f'<rect x="20" y="650" width="1085" height="62" rx="8" fill="#fff8e1" stroke="#e0c35a"/>'
    s += tx(32, 670, "READING THE FLOW", 12, 800, "#7a5a00") + tx(32, 688, wrapped(note_text, 175), 11.5, 400, "#3b3320", "start", 14)
    s += legend_journey2()
    return page_svg(s, title, subtitle, page_no, 2, "User Journey")


def legend_journey2():
    y = 757
    out = chip(40, y, "#ede7fb", "AI-assisted", stroke="#9b87d8", w=13) + chip(150, y, "#dbe9f9", "Hard rules", stroke="#6f9ad0", w=13)
    out += chip(250, y, "#e8f4ec", "Human", stroke="#8fc3a0", w=13) + chip(330, y, "#fff1dc", "Exception or fallback", stroke="#e0a040", w=13)
    out += chip(500, y, "#fff8e1", "Decision (diamond)", stroke="#d9b44a", w=13) + chip(655, y, "#fde7c7", "R1 = Round 1 problem", stroke="#e8a64a", w=13)
    out += tx(1083, y, "FR = requirement in the team's SRS v2", 11, 500, "#334155", "end")
    return out


def jr_page1():
    f = Flow()
    f.node("c0", 0, "C", "Hands over the list", "human")
    f.node("a0", 0, "A", "Uploads or pastes it", "human", "FR-001")
    f.node("s0", 0, "M", "Masks e-mail/phone, parses lines", "rules", "FR-002")
    f.node("s1", 1, "M", "AI available?", "decision", shape="diamond")
    f.node("s2", 2, "M", "Matches by meaning + hard rules", "ai", "FR-006-009")
    f.node("e2", 2, "E", "Rules-only match", "fallback", "FR-003")
    f.node("s3", 3, "M", "Converts units, checks stock", "rules", "FR-011-014")
    f.node("s4", 4, "M", "Flags exceptions first", "rules", "FR-010")
    f.node("a4", 4, "A", "Resolves lines with the customer", "human", "FR-015-016")
    f.node("c4", 4, "C", "Accepts or declines substitutes", "human", "FR-016")
    f.node("s5", 5, "M", "All lines resolved?", "decision", shape="diamond")
    f.edge([f.p("c0", "bottom"), f.p("a0", "top")])
    f.edge([f.p("a0", "bottom"), f.p("s0", "top")])
    f.edge([f.p("s0", "right"), f.p("s1", "left")])
    f.edge([f.p("s1", "right"), f.p("s2", "left")])
    f.tag(cx(1) + 34, 409, "Yes")
    f.edge([f.p("s1", "bottom"), (cx(1), ROWY["E"]), f.p("e2", "left")], color=AMBER_LINE)
    f.tag(cx(1) + 8, 496, "No", "start")
    f.edge([f.p("s2", "right"), f.p("s3", "left")])
    f.edge([f.p("e2", "right"), (cx(3), ROWY["E"]), f.p("s3", "bottom")], color=AMBER_LINE)
    f.edge([f.p("s3", "right"), f.p("s4", "left")])
    f.edge([f.p("s4", "top", -12), f.p("a4", "bottom", -12)])
    f.edge([f.p("a4", "bottom", 12), f.p("s4", "top", 12)])
    f.tag(cx(4) + 20, 366, "re-check", "start")
    resolve_loop(f, 4, 4, 4)
    f.edge([f.p("s4", "right"), f.p("s5", "left")])
    f.edge([f.p("s5", "top"), (cx(5), ROWY["A"]), f.p("a4", "right")])
    f.tag(cx(5) + 6, 350, "No", "start")
    back_half(f, 4)
    spans = [(0, 3, "Manual re-keying: about 12 min per list"), (4, 5, "Shift-dependent advice, lost sales"), (6, 9, "Fragmented systems: one standard order")]
    note = "Amber means an exception or fallback. Confirm stays blocked while any line is unresolved. If the AI is off, a rules-only match runs. If the POS refuses (503 or timeout), a CSV is written and the status is NEEDS_MANUAL, never POS_ACCEPTED."
    return journey_page("User journey 1: at the counter", "The associate serves the customer in person · SRS v2: UC1 to UC4", f, spans, note, 1)


def jr_page2():
    f = Flow()
    f.node("c0", 0, "C", "Sends the list by e-mail", "human", "UC5")
    f.node("a0", 0, "A", "Pastes the e-mail text", "human", "FR-022")
    f.node("s0", 0, "M", "Masks, matches, checks stock", "ai", "FR-006-015")
    f.node("a1", 1, "A", "Reviews lines, saves the quote", "human")
    f.node("s1", 1, "M", "Stores quote: price and stock snapshot", "rules", "FR-023-024")
    f.node("a2", 2, "A", "Sends reply and quote from own mailbox", "human")
    f.node("c2", 2, "C", "Approves outside SiteDesk", "human", "FR-039")
    f.node("a3", 3, "A", "Records approval on the quote", "human", "FR-022")
    f.node("s3", 3, "M", "Approved, not expired?", "decision", shape="diamond")
    f.node("e3", 3, "E", "Blocked: cannot prepare or confirm", "fallback")
    f.node("c4", 4, "C", "Returns on pick-up day", "human")
    f.node("a4", 4, "A", "Reopens the quote", "human")
    f.node("s4", 4, "M", "Re-checks live stock and price", "rules", "FR-025")
    f.node("a5", 5, "A", "Resolves lines with the customer", "human", "FR-016")
    f.node("c5", 5, "C", "Accepts substitutes", "human", "FR-039")
    f.node("s5", 5, "M", "All lines resolved?", "decision", shape="diamond")
    f.edge([f.p("c0", "bottom"), f.p("a0", "top")])
    f.edge([f.p("a0", "bottom"), f.p("s0", "top")])
    f.edge([f.p("s0", "right"), (gx(0, 1), ROWY["M"]), (gx(0, 1), ROWY["A"]), f.p("a1", "left")])
    f.edge([f.p("a1", "bottom"), f.p("s1", "top")])
    f.edge([f.p("s1", "right"), (gx(1, 2), ROWY["M"]), (gx(1, 2), ROWY["A"]), f.p("a2", "left")])
    f.edge([f.p("a2", "top"), f.p("c2", "bottom")])
    f.tag(cx(2) + 8, 232, "waits", "start")
    f.edge([f.p("c2", "right"), (gx(2, 3), ROWY["C"]), (gx(2, 3), ROWY["A"]), f.p("a3", "left")])
    f.edge([f.p("a3", "bottom"), f.p("s3", "top")])
    f.edge([f.p("s3", "right"), (gx(3, 4), ROWY["M"]), (gx(3, 4), ROWY["C"]), f.p("c4", "left")])
    f.tag(gx(3, 4) + 4, 392, "Yes", "start")
    f.edge([f.p("s3", "bottom"), f.p("e3", "top")], color=AMBER_LINE)
    f.tag(cx(3) + 14, 490, "No", "start")
    f.edge([f.p("c4", "bottom"), f.p("a4", "top")])
    f.edge([f.p("a4", "bottom"), f.p("s4", "top")])
    f.edge([f.p("s4", "right"), f.p("s5", "left")])
    f.edge([f.p("s5", "top", -14, 4), f.p("a5", "bottom", -14)])
    f.tag(cx(5) - 18, 366, "No", "end")
    f.edge([f.p("a5", "bottom", 14), f.p("s5", "top", 14, 8)])
    f.tag(cx(5) + 22, 366, "re-check", "start")
    resolve_loop(f, 5, 5, 5)
    back_half(f, 5)
    spans = [(0, 1, "Manual re-keying of e-mails"), (2, 3, "Customers wait for answers"), (4, 6, "Stock changes before pick-up cause wrong picks"), (7, 9, "Fragmented systems: one standard order")]
    note = "SiteDesk drafts the reply but sends no e-mail. Nothing is reserved between quote and pick-up, so the live re-check decides what can be promised. An e-mail request cannot be confirmed without its quote, and a quote cannot be prepared without a recorded approval."
    return journey_page("User journey 2: e-mail request to pick-up", "The customer is not at the counter · SRS v2: UC5", f, spans, note, 2)


if __name__ == "__main__":
    open(os.path.join(OUT, "System Diagram.html"), "w", encoding="utf-8").write(document("SiteDesk System Diagram", [sys_page1(), sys_page2()]))
    open(os.path.join(OUT, "User Journey.html"), "w", encoding="utf-8").write(document("SiteDesk User Journey", [jr_page1(), jr_page2()]))
    print("written")
