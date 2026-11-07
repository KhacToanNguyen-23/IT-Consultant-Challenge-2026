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
    s += box(880, 200, 200, 130, "LLM API provider", ["Optional; off in this demo"], fill="#eef0f3", stroke=GREY, dash=True, tcolor="#374151", r=2, sub="External entity")
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
    s += box(590, 150, 235, 320, "Core API", [
        "Parse + PII masking · FR-001/002", "Matcher + hard rules · FR-006 to 009", "Convert, stock, alternatives · FR-011 to 016",
        "Quotes, orders, idempotency · FR-018 to 028", "CSV when the POS is down · FR-019", "Telemetry, KPI queries · FR-029 to 031", "",
        "In-process modules:", "AI Gateway · Local Connector"], fill=BLUE, sub="FastAPI (Python)", lsize=11)
    s += '<rect x="606" y="396" width="203" height="58" rx="8" fill="#e9f3ff" stroke="#9bc5e5" stroke-width="2"/>'
    s += tx(707, 418, "Local embedding model", 12, 700, NAVY, "middle")
    s += tx(707, 436, "multilingual-e5-small · no data leaves", 11, 400, "#244a6e", "middle")
    s += box(305, 340, 180, 160, "SiteDesk DB", ["Catalog + vectors,", "sessions, quotes,", "decisions, audit"], fill=GREEN, sub="PostgreSQL 15 + pgvector", lsize=11)
    s += box(920, 150, 185, 100, "LLM API", ["Optional, masked", "text only"], fill="#eef0f3", stroke=GREY, dash=True, tcolor="#374151", sub="External · optional")
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


# ============================================================ USER JOURNEY
LANES = [("Customer", 98), ("Counter associate", 240), ("SiteDesk", 382)]
LANE_H = 142
X0, BW, GAP = 60, 104, 13
ROLE = {"human": ("#e8f4ec", "#8fc3a0"), "rules": ("#dbe9f9", "#6f9ad0"), "ai": ("#ede7fb", "#9b87d8")}


def colx(c):
    return X0 + c * (BW + GAP)


def lanes():
    s = ""
    for i, (name, y) in enumerate(LANES):
        s += f'<rect x="20" y="{y}" width="1085" height="{LANE_H}" fill="{"#f8fafd" if i % 2 == 0 else "#f1f5fb"}" stroke="#d3deec"/>'
        s += f'<rect x="20" y="{y}" width="30" height="{LANE_H}" fill="{NAVY}"/>'
        s += f'<text transform="translate(41,{y + LANE_H / 2}) rotate(-90)" font-size="12.5" font-weight="700" fill="#fff" text-anchor="middle">{esc(name)}</text>'
    return s


def step(col, lane, n, text, tag, role, bh=124):
    x = colx(col)
    y = LANES[lane][1] + (LANE_H - bh) / 2
    fill, stroke = ROLE[role]
    s = f'<rect x="{x}" y="{y}" width="{BW}" height="{bh}" rx="8" fill="{fill}" stroke="{stroke}" stroke-width="1.8"/>'
    s += f'<circle cx="{x + 12}" cy="{y + 12}" r="10" fill="{NAVY}"/>' + tx(x + 12, y + 16, str(n), 11.5, 800, "#fff", "middle")
    s += tx(x + 8, y + 36, wrapped(text, 15), 11, 500, "#17202c", "start", 13)
    s += tx(x + 8, y + bh - 8, tag, 10.5, 700, "#1f4f86")
    return s, (x, y, BW, bh)


def connect(a, b):
    xa, ya, wa, ha = a
    xb, yb, wb, hb = b
    x1, y1 = xa + wa, ya + ha / 2
    x2, y2 = xb, yb + hb / 2
    if abs(y1 - y2) < 1:
        return arrow([(x1, y1), (x2, y2)])
    mid = x1 + GAP / 2
    return arrow([(x1, y1), (mid, y1), (mid, y2), (x2, y2)])


def r1_band(spans):
    y, h = 536, 40
    s = f'<rect x="20" y="{y}" width="1085" height="{h}" fill="#fff8ec" stroke="#f0d3a0"/>'
    s += f'<rect x="20" y="{y}" width="30" height="{h}" fill="#e8a64a"/>' + tx(35, y + 25, "R1", 12, 800, "#fff", "middle")
    for c1, c2, text in spans:
        x = colx(c1)
        w = colx(c2) + BW - x
        s += f'<rect x="{x}" y="{y + 5}" width="{w}" height="{h - 10}" rx="6" fill="#fde7c7" stroke="#e8a64a"/>'
        lines = wrapped(text, int((w - 12) / 5.6))[:2]
        s += tx(x + w / 2, y + 19 if len(lines) == 1 else y + 16, lines, 10.5, 600, "#7a4300", "middle", 11.5)
    return s


def journey(title, subtitle, steps, spans, alts, strip, page_no):
    s = lanes()
    rects = []
    for col, (lane, text, tag, role) in enumerate(steps):
        frag, r = step(col, lane, col + 1, text, tag, role)
        s += frag
        rects.append(r)
    for i in range(len(rects) - 1):
        s += connect(rects[i], rects[i + 1])
    s += r1_band(spans)
    s += tx(20, 598, "Alternative paths and guardrails", 13, 800, AMBER)
    n = len(alts)
    wdt = (1085 - (n - 1) * 12) / n
    for i, (head, body) in enumerate(alts):
        x = 20 + i * (wdt + 12)
        s += f'<rect x="{x}" y="606" width="{wdt}" height="70" rx="8" fill="#fff4e5" stroke="#f0b866"/>'
        s += tx(x + 10, 624, head, 12, 800, "#8a4b00")
        s += tx(x + 10, 641, wrapped(body, int((wdt - 20) / 5.7)), 11, 400, "#3b2a10", "start", 13.4)
    s += '<rect x="20" y="686" width="1085" height="56" rx="8" fill="#e8f4ec" stroke="#8fc3a0"/>'
    s += tx(32, 704, strip[0], 12, 800, "#1f6b3f")
    s += tx(32, 721, wrapped(strip[1], 165), 11, 400, "#1f3a2a", "start", 13.4)
    s += legend_journey()
    return page_svg(s, title, subtitle, page_no, 2, "User Journey")


def jr_page1():
    steps = [
        (0, "Hands over the list (PDF, pasted or e-mail text)", "UC1", "human"),
        (1, "Uploads or pastes it, then Read list", "FR-001 intake", "human"),
        (2, "Masks e-mail and phone; reads every line, keeps unreadable ones", "FR-002 masking", "rules"),
        (2, "Matches SKUs by meaning, converts units, checks live stock", "FR-006-014 match", "ai"),
        (1, "Reviews exceptions; Confirm blocked until all resolved", "FR-010 gate", "human"),
        (2, "Short or out of stock: safe alternative with price difference", "FR-015 options", "rules"),
        (0, "Accepts or declines the alternative", "FR-016 consent", "human"),
        (1, "Chooses client or walk-in, then Confirm", "FR-017-018 order", "human"),
        (2, "POS accepts: reference. POS down: CSV, same reference", "FR-019 POS or CSV", "rules"),
    ]
    spans = [(1, 3, "Manual re-keying: every line typed by hand, about 12 min per list (Round 1 estimate)"),
             (4, 4, "Shift-dependent advice"),
             (5, 6, "Lost sales: \"sorry, out of stock\""),
             (7, 8, "Fragmented systems: one connector, CSV fallback")]
    alts = [
        ("AI is off", "Hard rules and manual catalog search keep the counter running; suggestions are labelled rule-based (FR-003, 033)."),
        ("Line is not an order line", "The associate removes it (title, greeting). The last remaining line cannot be removed."),
        ("Customer declines", "A reason is recorded and the line stays open; the SKU never changes without agreement (FR-016)."),
        ("POS is down", "CSV export with the same reference; status NEEDS_MANUAL; the associate keys it into the legacy POS."),
    ]
    strip = ("Value shown on the receipt of every order",
             "Sales rescued by substitutes · time from upload to Confirm. Measured per order on simulated data; Round 1 targets are not claimed as results.")
    return journey("User journey 1: at the counter, from list to confirmed order", "The associate serves the customer in person. SRS v2: UC1 to UC4, FR-001 to FR-020.", steps, spans, alts, strip, 1)


def jr_page2():
    steps = [
        (0, "Sends the material list by e-mail", "UC5", "human"),
        (1, "Copies the e-mail text into SiteDesk (E-mail quote)", "FR-022 e-mail", "human"),
        (2, "Masks, matches, checks stock; short lines get alternatives", "FR-006-015 match", "ai"),
        (1, "Copy reply to customer; sends it from own mailbox", "no e-mail sent", "human"),
        (0, "Agrees by e-mail or phone, outside SiteDesk", "FR-039 consent", "human"),
        (2, "Save quote: price and stock snapshot, not reserved", "FR-023-024 quote", "rules"),
        (1, "Records the customer's approval on the quote (channel)", "FR-022 approval", "human"),
        (2, "Pick-up day: re-check live stock and price, show changes", "FR-025 re-check", "rules"),
        (1, "Customer accepts substitutes; Pick slip; Confirm to POS or CSV", "FR-026-028", "human"),
    ]
    spans = [(1, 2, "Manual re-keying of e-mailed lists"),
             (3, 4, "Customers wait for answers; advice depends on the shift"),
             (5, 7, "Stock changes between order and pick-up cause wrong picks and re-deliveries"),
             (8, 8, "Fragmented systems")]
    alts = [
        ("No quote, no Confirm", "An e-mail request cannot be confirmed without its quote (QUOTE_REQUIRED)."),
        ("No approval, no Prepare", "Sending the quote is not approval: Prepare is refused until the customer's approval is recorded."),
        ("Stock changed since the quote", "Short lines are marked; the substitute is accepted now, or an earlier agreement is recorded."),
        ("Quote expires or is cancelled", "Expiry is evaluated when the quote is opened; an expired or cancelled quote cannot be confirmed."),
    ]
    strip = ("Why this journey matters",
             "Nothing is reserved between the quote and the pick-up, so the live re-check is what keeps promises honest. The yard can prepare with the Pick slip before the customer arrives (Round 1, 07:00 pre-pick).")
    return journey("User journey 2: e-mail request to pre-order and pick-up", "The customer is not at the counter. SRS v2: UC5, FR-022 to FR-028, FR-039 and FR-040.", steps, spans, alts, strip, 2)


if __name__ == "__main__":
    open(os.path.join(OUT, "System Diagram.html"), "w", encoding="utf-8").write(document("SiteDesk System Diagram", [sys_page1(), sys_page2()]))
    open(os.path.join(OUT, "User Journey.html"), "w", encoding="utf-8").write(document("SiteDesk User Journey", [jr_page1(), jr_page2()]))
    print("written")
