"""A/B check of the OPTIONAL LLM attribute-extraction step on the D22 evaluation lines.

    LLM_API_KEY=... LLM_BASE_URL=... LLM_MODEL=... python -m scripts.evaluate_llm      (inside the backend container)

For every line the rules/embedding pipeline runs twice: LLM off, and LLM on for the lines the rules find ambiguous
(unknown category or a missing must-match attribute) - exactly what pipeline.enrich_with_llm does in production.
Reports only measured facts: accuracy with/without, calls, latency, tokens, and every line whose result changed.
The key is read from the environment and never printed. Do not quote the numbers as "NFR-005": the labels are
AI-drafted and not human-reviewed.
"""
import json
import statistics
import sys
import time
import uuid
from pathlib import Path

from ai import llm
from db.database import SessionLocal
from db.models import SessionLine
from services import matcher, parser, pipeline, retrieval

EVAL = Path(__file__).resolve().parents[1] / "seeds" / "evaluation.jsonl"


class _Recorder:
    """Stands in for the DB session: collects the AiInvocation rows the pipeline would store."""

    def __init__(self):
        self.rows = []

    def add(self, row):
        self.rows.append(row)


def _line(text: str) -> SessionLine:
    parsed = parser.parse_line(text)
    return SessionLine(line_id=uuid.uuid4(), session_id=uuid.uuid4(), line_no=1, raw_customer_input=text,
                       parsed_name=parsed.item_text or "", parse_status=parsed.status, attributes={})


def _match(db, products, line, attrs):
    clean = {k: v for k, v in attrs.items() if k != "length_hint" and not k.startswith("_")}
    sem, _ = retrieval.semantic_candidates(db, [line.parsed_name], [clean.get("category")])
    return matcher.match(line.parsed_name, clean, list(products.values()), sem[0])


def _ok(case, cands):
    top = cands[0] if cands else None
    if case["must_clarify"]:
        return top is None or top["band"] != "HIGH"
    return bool(top) and top["sku"] in set(case["expected_skus"])


def main() -> int:
    if llm.get() is None:
        print("LLM is disabled: set LLM_API_KEY, LLM_BASE_URL and LLM_MODEL in the environment of this command.")
        return 2
    from ai import embedding

    if embedding.load() is None:  # this is a separate process from the API: load the real model here too
        print("embedding model could not be loaded; this A/B needs the vector retrieval of the real pipeline.")
        return 3
    cases = [json.loads(l) for l in EVAL.read_text(encoding="utf-8").splitlines() if l.strip()]
    rows, latencies, tokens_in, tokens_out, dropped = [], [], 0, 0, 0
    with SessionLocal() as db:
        products = pipeline.load_products(db)
        for c in cases:
            line = _line(c["text"])
            base_attrs = pipeline.line_attrs(line)
            if not pipeline.is_ambiguous(base_attrs):
                continue  # the LLM is never asked about clear lines
            before = _match(db, products, line, base_attrs)
            llm_attrs = dict(base_attrs)
            rec = _Recorder()
            t = time.perf_counter()
            info = pipeline.enrich_with_llm(rec, [line], {line.line_id: llm_attrs})
            latencies.append((time.perf_counter() - t) * 1000)
            for r in rec.rows:
                tokens_in += r.input_tokens or 0
                tokens_out += r.output_tokens or 0
                dropped += 1 if "dropped=" in (r.status or "") else 0
            after = _match(db, products, line, llm_attrs)
            rows.append({"id": c["id"], "text": c["text"], "kind": c["kind"], "calls": info["llm_calls"],
                         "added": llm_attrs.get("_llm", []), "before_ok": _ok(c, before), "after_ok": _ok(c, after),
                         "before": [x["sku"] for x in before][:2], "after": [x["sku"] for x in after][:2],
                         "band_before": before[0]["band"] if before else "NONE", "band_after": after[0]["band"] if after else "NONE",
                         "status": [r.status for r in rec.rows]})
    n = len(rows)
    print(f"provider={llm.status()}  ambiguous lines asked: {n}/{len(cases)}  "
          f"calls={sum(r['calls'] for r in rows)}  tokens in/out={tokens_in}/{tokens_out}  fields dropped for missing evidence (lines)={dropped}")
    if latencies:
        lat = sorted(latencies)
        print(f"latency per LLM line: p50={statistics.median(lat):.0f} ms  p95={lat[int(0.95 * (len(lat) - 1))]:.0f} ms  max={lat[-1]:.0f} ms")
    print(f"correct on these lines: LLM off {sum(r['before_ok'] for r in rows)}/{n}  ->  LLM on {sum(r['after_ok'] for r in rows)}/{n}")
    errors = [r for r in rows if any(not s.startswith("ok") for s in r["status"])]
    print(f"calls that fell back to rules (error / bad JSON): {len(errors)}")
    changed = [r for r in rows if r["before"] != r["after"] or r["band_before"] != r["band_after"] or r["added"]]
    print(f"lines where the LLM changed something: {len(changed)}")
    for r in changed:
        mark = "BETTER" if (not r["before_ok"] and r["after_ok"]) else "WORSE" if (r["before_ok"] and not r["after_ok"]) else "same"
        print(f"  [{mark:6}] {r['id']} {r['text'][:46]!r:50} added={r['added']} {r['band_before']}{r['before']} -> {r['band_after']}{r['after']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
