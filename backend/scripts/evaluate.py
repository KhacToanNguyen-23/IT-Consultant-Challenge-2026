"""D22 evaluation (SRS v2 §11.1) + NFR-003 performance.

Usage (inside backend container):
  python -m scripts.evaluate                 # accuracy report, embedding vs rules fallback
  python -m scripts.evaluate --perf 20       # + 20-line analyze timing over N runs via the real API
Writes reports/evaluation_<UTC date>.md and .json. Report says "initial results on N lines" (<150 → no NFR-05 claim).
"""
import json
import math
import platform
import statistics
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from ai import embedding
from config import settings
from db.database import SessionLocal
from services import matcher, parser, pipeline, retrieval

ROOT = Path(__file__).resolve().parents[1]
EVAL = ROOT / "seeds" / "evaluation.jsonl"


def wilson_upper(err: int, n: int, z: float = 1.96) -> float:
    if n == 0:
        return float("nan")
    p = err / n
    return (p + z * z / (2 * n) + z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / (1 + z * z / n)


def run(cases, products, db, use_embedding: bool):
    rows = []
    parsed = [parser.parse_line(c["text"]) for c in cases]
    names = [p.item_text or "" for p in parsed]
    attrs = [parser.extract_attributes(n) for n in names]
    t = time.perf_counter()
    if use_embedding:
        sem, _ = retrieval.semantic_candidates(db, names, [a.get("category") for a in attrs])
    else:
        sem = [None] * len(cases)
    for c, n, a, s in zip(cases, names, attrs, sem):
        cands = matcher.match(n, a, list(products.values()), s)
        top = cands[0] if cands else None
        b = top["band"] if top else "NONE"
        exp = set(c["expected_skus"])
        if c["must_clarify"]:
            ok = b != "HIGH"  # correct behaviour = not auto-accepted
            in_top3 = (not exp) or any(x["sku"] in exp for x in cands)
        else:
            ok = bool(top) and top["sku"] in exp
            in_top3 = any(x["sku"] in exp for x in cands)
        rows.append({**c, "parsed_name": n, "attrs": {k: v for k, v in a.items()}, "top1": top["sku"] if top else None,
                     "score": top["score"] if top else None, "band": b, "ok": ok, "in_top3": in_top3,
                     "offered": [x["sku"] for x in cands],
                     "wrong_high": b == "HIGH" and (c["must_clarify"] or top["sku"] not in exp)})
    return rows, round((time.perf_counter() - t) * 1000, 1)


def summarize(rows):
    s = {"n": len(rows)}
    by_band = defaultdict(list)
    for r in rows:
        by_band[r["band"]].append(r)
    s["bands"] = {b: {"count": len(v), "top1_correct": sum(r["ok"] for r in v),
                      "error_rate": round(1 - sum(r["ok"] for r in v) / len(v), 3)} for b, v in sorted(by_band.items())}
    high = by_band.get("HIGH", [])
    wh = sum(r["wrong_high"] for r in high)
    s["high_band"] = {"count": len(high), "wrong": wh, "error_rate": round(wh / len(high), 4) if high else None,
                      "wilson_upper95": round(wilson_upper(wh, len(high)), 4) if high else None}
    match_rows = [r for r in rows if not r["must_clarify"]]
    s["top1_accuracy_answerable"] = round(sum(r["ok"] for r in match_rows) / len(match_rows), 3) if match_rows else None
    s["top3_recall_answerable"] = round(sum(r["in_top3"] for r in match_rows) / len(match_rows), 3) if match_rows else None
    s["coverage_high_answerable"] = round(sum(r["band"] == "HIGH" for r in match_rows) / len(match_rows), 3) if match_rows else None
    clar = [r for r in rows if r["must_clarify"]]
    s["clarify_correct"] = f"{sum(r['ok'] for r in clar)}/{len(clar)}"
    traps = [r for r in rows if r["kind"] == "trap"]
    s["unsafe_offers_on_traps"] = sum(bool(r["offered"]) for r in traps)
    s["by_language"] = {}
    for lang in sorted({r["language"] for r in rows}):
        v = [r for r in rows if r["language"] == lang]
        s["by_language"][lang] = {"n": len(v), "correct": sum(r["ok"] for r in v), "wrong_high": sum(r["wrong_high"] for r in v)}
    s["by_kind"] = {k: f"{sum(r['ok'] for r in rows if r['kind'] == k)}/{sum(r['kind'] == k for r in rows)}"
                    for k in sorted({r["kind"] for r in rows})}
    return s


def perf(runs: int):
    import httpx

    lines = [c["text"] for c in map(json.loads, EVAL.read_text(encoding="utf-8").splitlines()) if c["kind"] in ("easy", "other_lang")][:20]
    text = "\n".join(lines)
    out = []
    with httpx.Client(base_url="http://localhost:8000/api/v1", timeout=30) as c:
        sid = c.post("/sessions", json={"input_type": "paste_text"}).json()["session_id"]
        c.post(f"/sessions/{sid}/ingest", json={"text": text})
        c.post(f"/sessions/{sid}/analyze", json={})  # warm-up
        for _ in range(runs):
            t = time.perf_counter()
            r = c.post(f"/sessions/{sid}/analyze", json={}).json()
            out.append({"wall_ms": (time.perf_counter() - t) * 1000, **r["stage_timings_ms"]})
    walls = sorted(x["wall_ms"] for x in out)
    p95 = walls[min(len(walls) - 1, math.ceil(0.95 * len(walls)) - 1)]
    return {"lines": len(lines), "runs": runs, "p50_ms": round(statistics.median(walls), 1), "p95_ms": round(p95, 1),
            "max_ms": round(walls[-1], 1), "mode": out[-1].get("match_mode"),
            "stage_p50_ms": {k: round(statistics.median(x[k] for x in out), 1) for k in ("embed_ms", "vector_ms", "stock_ms", "rules_convert_alternatives_ms")}}


def main():
    cases = [json.loads(l) for l in EVAL.read_text(encoding="utf-8").splitlines() if l.strip()]
    with SessionLocal() as db:
        products = pipeline.load_products(db)
        if embedding.get() is None:
            embedding.load()
            retrieval.reindex(db, only_missing=True)
        emb_rows, emb_ms = run(cases, products, db, True)
        rule_rows, rule_ms = run(cases, products, db, False)
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "n": len(cases), "reviewed_labels": sum(c.get("reviewed", False) for c in cases),
        "config": {"embedding": embedding.status(), "high": settings.high_threshold, "review": settings.review_threshold,
                   "gap": settings.ambiguity_gap, "catalog_size": len(products)},
        "hardware": {"platform": platform.platform(), "python": platform.python_version(), "cpu_count": __import__("os").cpu_count()},
        "embedding_mode": {"summary": summarize(emb_rows), "batch_ms": emb_ms},
        "rules_fallback_mode": {"summary": summarize(rule_rows), "batch_ms": rule_ms},
    }
    if "--perf" in sys.argv:
        report["performance_20_lines"] = perf(int(sys.argv[sys.argv.index("--perf") + 1]))
    out_dir = ROOT / "reports"
    out_dir.mkdir(exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    (out_dir / f"evaluation_{stamp}.json").write_text(json.dumps({**report, "rows_embedding": emb_rows, "rows_rules": rule_rows},
                                                                 ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    (out_dir / f"evaluation_{stamp}.md").write_text(to_md(report, emb_rows), encoding="utf-8")
    print(json.dumps({k: report[k] for k in report if k not in ()}, ensure_ascii=False, indent=1, default=str))


def to_md(r, emb_rows):
    e, f = r["embedding_mode"]["summary"], r["rules_fallback_mode"]["summary"]
    hb = e["high_band"]
    lines = [
        f"# SiteDesk — SKU matching evaluation (initial results on {r['n']} lines)",
        "",
        f"Generated {r['generated_at']} · labels human-reviewed: **{r['reviewed_labels']}/{r['n']}** · catalog {r['config']['catalog_size']} SKU (simulated)",
        f"Embedding: `{r['config']['embedding']['provider']}/{r['config']['embedding']['model']}` · thresholds high >{r['config']['high']}, review ≥{r['config']['review']}, gap {r['config']['gap']}",
        f"Hardware: {r['hardware']['platform']}, {r['hardware']['cpu_count']} CPU",
        "",
        "> Fewer than 150 labelled lines: these are **initial results**, NFR-05 (high-band false match ≤2%) is NOT claimed as met.",
        "> Labels were drafted with AI assistance; numbers are only quotable after a teammate reviews every row (`reviewed` flag).",
        "",
        "| Metric | Embedding + hard rules | Rules-only fallback (AI fail) |",
        "|---|---|---|",
        f"| Top-1 accuracy (answerable lines) | {e['top1_accuracy_answerable']} | {f['top1_accuracy_answerable']} |",
        f"| Correct SKU in top-3 | {e['top3_recall_answerable']} | {f['top3_recall_answerable']} |",
        f"| High-band coverage (zero-touch potential) | {e['coverage_high_answerable']} | {f['coverage_high_answerable']} |",
        f"| High band: wrong / count | {hb['wrong']}/{hb['count']} | {f['high_band']['wrong']}/{f['high_band']['count']} |",
        f"| High band error, Wilson 95% upper | {hb['wilson_upper95']} | {f['high_band']['wilson_upper95']} |",
        f"| Must-clarify lines correctly NOT auto-accepted | {e['clarify_correct']} | {f['clarify_correct']} |",
        f"| Trap lines where any SKU was offered (should be 0) | {e['unsafe_offers_on_traps']} | {f['unsafe_offers_on_traps']} |",
        "",
        "## Embedding mode by band", "", "| Band | Count | Correct | Error rate |", "|---|---|---|---|",
        *[f"| {b} | {v['count']} | {v['top1_correct']} | {v['error_rate']} |" for b, v in e["bands"].items()],
        "", "## By language (embedding mode)", "", "| Lang | n | Correct | Wrong-high |", "|---|---|---|---|",
        *[f"| {k} | {v['n']} | {v['correct']} | {v['wrong_high']} |" for k, v in e["by_language"].items()],
        "", "## By case type (embedding mode)", "", *[f"- **{k}**: {v}" for k, v in e["by_kind"].items()],
    ]
    if "performance_20_lines" in r:
        p = r["performance_20_lines"]
        lines += ["", "## Performance — analyze 20 lines (NFR-003 target ≤3.0 s after warm-up)", "",
                  f"{p['runs']} runs, mode `{p['mode']}`: p50 **{p['p50_ms']} ms**, p95 **{p['p95_ms']} ms**, max {p['max_ms']} ms.",
                  f"Stage p50: {p['stage_p50_ms']}. External LLM not used in the matching path."]
    wrong = [x for x in emb_rows if not x["ok"]]
    lines += ["", f"## Misses in embedding mode ({len(wrong)})", "", "| id | text | kind | expected | got | band |", "|---|---|---|---|---|---|",
              *[f"| {x['id']} | {x['text']} | {x['kind']} | {', '.join(x['expected_skus']) or '— (no SKU)'} | {x['top1'] or '—'} | {x['band']} |" for x in wrong]]
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    main()
