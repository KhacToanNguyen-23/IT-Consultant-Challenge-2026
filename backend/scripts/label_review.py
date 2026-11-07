"""Human review of the evaluation labels (SRS v2 NFR-05, D22).

    python -m scripts.label_review export   # writes docs/label-review-sheet.csv (open in Excel / Google Sheets)
    python -m scripts.label_review apply    # reads the filled sheet, updates seeds/evaluation.jsonl, prints a summary

How to review a row: read the customer text, look at the product name(s) in "expected_products" and decide whether
that is the correct answer. For rows with no expected product ("must_clarify" / trap / absent) decide whether the
system must NOT pick a product automatically.
  verdict  = OK            the label is right
             FIX           the label is wrong; write the correct SKU(s) in "correct_skus" (comma separated),
                           or write NONE if no product may be chosen automatically
             (blank)       not reviewed yet: the row stays reviewed=false
Never run seeds/build_evaluation.py after a review: it regenerates the file and resets every reviewed flag.
"""
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
JSONL = ROOT / "backend" / "seeds" / "evaluation.jsonl"
CATALOG = ROOT / "mock-pos" / "seeds" / "catalog.json"
SHEET = ROOT / "docs" / "label-review-sheet.csv"
COLUMNS = ["id", "language", "kind", "customer_text", "expected_skus", "expected_products", "must_clarify", "note", "verdict", "correct_skus", "reviewer_comment"]


def load_cases():
    return [json.loads(line) for line in JSONL.read_text(encoding="utf-8").splitlines() if line.strip()]


def names():
    data = json.loads(CATALOG.read_text(encoding="utf-8"))
    items = data if isinstance(data, list) else data.get("items", [])
    return {i["sku"]: i["name"] for i in items}


def export():
    nm = names()
    rows = load_cases()
    with SHEET.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(COLUMNS)
        for c in rows:
            skus = c.get("expected_skus") or []
            products = " | ".join(nm.get(s, "?") for s in skus) if skus else "(none: must NOT be auto-matched)"
            w.writerow([c["id"], c["language"], c["kind"], c["text"], ", ".join(skus) if skus else "NONE", products,
                        "yes" if c.get("must_clarify") else "no", c.get("note", ""), "", "", ""])
    print(f"wrote {SHEET} ({len(rows)} rows). Fill the 'verdict' column with OK or FIX, save as CSV, then run: apply")


def apply():
    cases = {c["id"]: c for c in load_cases()}
    order = list(cases)
    reviewed = fixed = 0
    unknown = []
    with SHEET.open(encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            v = (r.get("verdict") or "").strip().upper()
            c = cases.get(r["id"])
            if not v or c is None:
                continue
            if v == "OK":
                c["reviewed"] = True
                reviewed += 1
            elif v == "FIX":
                raw = (r.get("correct_skus") or "").strip()
                if not raw:
                    print(f"{r['id']}: FIX without correct_skus, skipped")
                    continue
                new = [] if raw.upper() == "NONE" else [s.strip() for s in raw.split(",") if s.strip()]
                bad = [s for s in new if s not in names()]
                if bad:
                    unknown.append((r["id"], bad))
                    continue
                c["expected_skus"] = new
                c["reviewed"] = True
                c["note"] = (c.get("note", "") + " | label corrected in human review").strip(" |")
                reviewed += 1
                fixed += 1
            else:
                print(f"{r['id']}: unknown verdict '{v}', skipped")
    JSONL.write_text("".join(json.dumps(cases[i], ensure_ascii=False) + "\n" for i in order), encoding="utf-8")
    total = len(order)
    done = sum(1 for c in cases.values() if c.get("reviewed"))
    print(f"reviewed this run: {reviewed} (labels corrected: {fixed}); human-reviewed in total: {done}/{total}")
    if unknown:
        print("rows skipped because a SKU does not exist in the catalog:", unknown)
    print("Now re-run the report:  python -m scripts.evaluate")


if __name__ == "__main__":
    {"export": export, "apply": apply}.get(sys.argv[1] if len(sys.argv) > 1 else "", lambda: print(__doc__))()
