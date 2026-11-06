"""Flow 1 acceptance run against a LIVE stack (SRS §11.4 smoke / demo-ok tag).

    python -m scripts.acceptance_flow1                       # inside the backend container
    python backend/scripts/acceptance_flow1.py               # from the host, API on http://localhost:8000
    SITEDESK_API=http://localhost:8000 python backend/scripts/acceptance_flow1.py

Standard library only. Exit code 0 = every check passed. It creates sessions in the demo database (harmless) and
always restores both fail toggles. Each check is labelled with the SRS requirement it evidences.
"""
import json
import os
import sys
import time
import urllib.error
import urllib.request
import uuid

API = os.getenv("SITEDESK_API", "http://localhost:8000").rstrip("/") + "/api/v1"
RESULTS: list[tuple[str, bool, str]] = []


def call(method, path, body=None, raw=None, ctype="application/json", timeout=60, headers=None):
    data = raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
    req = urllib.request.Request(API + path, data=data, method=method,
                                 headers={"Content-Type": ctype, **(headers or {})})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            payload = r.read()
            return r.status, _loads(payload)
    except urllib.error.HTTPError as e:
        return e.code, _loads(e.read())


def _loads(b):
    try:
        value = json.loads(b)
        return value if isinstance(value, dict) else {"_value": value}
    except Exception:  # noqa: BLE001 - a non-JSON body (e.g. a bare 500) is a failed check, never a crash
        return {"_raw": b.decode("utf-8", "replace")[:200]}


def call_text(path):
    req = urllib.request.Request(API + path, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")


def check(label, ok, detail=""):
    RESULTS.append((label, bool(ok), str(detail)[:140]))


def err_code(r):
    return r[1].get("error", {}).get("code") if isinstance(r[1], dict) else None


def open_session(text):
    sid = call("POST", "/sessions", {"input_type": "paste_text", "market": "DK"})[1]["session_id"]
    st, v = call("POST", f"/sessions/{sid}/ingest", {"text": text})
    return sid, st, v


def view(sid):
    return call("GET", f"/sessions/{sid}")[1]


def confirm(sid, body=None, key=None):
    key = key or view(sid)["order_session_id"]
    return call("POST", f"/sessions/{sid}/confirm", {} if body is None else body,
                headers={"Idempotency-Key": key})


def resolve_all(sid):
    """Do what the associate does: add missing qty/unit, keep or choose a SKU for every blocked line."""
    for _ in range(3):
        v = view(sid)
        todo = [l for l in v["lines"] if l["line_status"] == "NEEDS_CLARIFICATION" or not (l.get("conversion") or {}).get("selling_quantity")]
        if not todo:
            return v
        for l in todo:
            p = l.get("parsed") or {}
            if p.get("quantity") is None or p.get("unit") is None:
                call("PATCH", f"/sessions/{sid}/lines/{l['line_no']}",
                     {"requested_qty": p.get("quantity") or 1, "requested_unit": p.get("unit") or "piece"})
                l = next(x for x in view(sid)["lines"] if x["line_no"] == l["line_no"])
            sku = l.get("final_sku") or ((l.get("match") or {}).get("candidates") or [{}])[0].get("sku") or "SKU-DK-4595-480"
            call("PUT", f"/sessions/{sid}/lines/{l['line_no']}/selection",
                 {"sku": sku, "decision": "SKU_KEPT" if l.get("final_sku") else "SKU_EDITED"})
    return view(sid)


def multipart(name, content):
    b = uuid.uuid4().hex
    body = (f'--{b}\r\nContent-Disposition: form-data; name="file"; filename="{name}"\r\n'
            "Content-Type: application/octet-stream\r\n\r\n").encode() + content + f"\r\n--{b}--\r\n".encode()
    return body, f"multipart/form-data; boundary={b}"


def upload(name, content):
    """Create a file session and POST one multipart file; returns (status, json)."""
    sid = call("POST", "/sessions", {"input_type": "file", "market": "DK"})[1]["session_id"]
    body, ctype = multipart(name, content)
    return call("POST", f"/sessions/{sid}/ingest", raw=body, ctype=ctype)


ORDER = "120 m timber 45x95 C24\n5 poser cement 25 kg\n10 x 4.8m timber 45x95 C24"


def main() -> int:
    call("POST", "/admin/fail-modes", {"ai": False, "pos": False})
    try:
        st, h = call("GET", "/health")
        check("NFR-001 stack healthy (db, embedding, mock-pos)", st == 200 and h.get("status") == "healthy", h if st != 200 else h.get("status"))

        # ---- intake, PII, units (FR-001/002/005/011)
        sid, st, v = open_session("ring +45 22 33 44 55\n10 plader gips vådrum 12.5 mm\n120 m timber 45x95 C24 - mail kunde@firma.dk")
        check("FR-002 phone/e-mail masked, no merged or lost lines", st == 200 and v["read_line_count"] == 2
              and "22 33 44 55" not in str(v) and "kunde@firma.dk" not in str(v), f"lines={v.get('read_line_count')}")
        check("FR-001 damaged PDF -> 422 (not 500)", err_code(upload("a.pdf", b"%PDF-1.4 junk")) in ("UNREADABLE_FILE", "SCAN_ONLY_PDF"))
        check("FR-001 unsupported file -> 422 UNSUPPORTED_FILE", err_code(upload("a.exe", b"MZ\x90")) == "UNSUPPORTED_FILE")
        check("FR-001 empty file -> 422 NO_TEXT", err_code(upload("empty.txt", b"   ")) == "NO_TEXT")
        check("FR-001 oversized file -> 413 TOO_LARGE", err_code(upload("big.txt", b"x" * (5 * 1024 * 1024 + 10))) == "TOO_LARGE")
        ok_csv = upload("order.csv", b"vare;antal\ntimber 45x95 C24;120\ncement 25 kg;5\n")
        check("FR-001 CSV with a header row is read (2 lines)", ok_csv[0] == 200 and ok_csv[1].get("read_line_count") == 2, ok_csv[1].get("read_line_count"))
        units = "\n".join(f"12 {u} gips 12.5 mm" for u in ("sheet", "palle", "förp", "lpm", "stk"))
        _, _, vu = open_session(units)
        got = [l["parsed"]["unit"] for l in vu["lines"]]
        check("FR-011 SRS 15.2 units (sheet, pallet, pack, linear metre, piece)", got == ["sheet", "pallet", "pack", "linear_metre", "piece"], got)
        _, _, vm = open_session("20 m isolering 95 mm")
        check("FR-011 bare 'm' outside timber/decking is not guessed", vm["lines"][0]["parsed"]["unit"] is None and "ambiguous_unit_m" in vm["lines"][0]["parsed"]["warnings"])
        s3 = call("POST", "/sessions", {"input_type": "paste_text", "market": "DK"})[1]["session_id"]
        check("API strict bodies: unknown field -> 422", err_code(call("PATCH", f"/sessions/{s3}/lines/1", {"quantity": 5})) == "VALIDATION")

        # ---- matching and hard rules (FR-007/008/009/013)
        sid, _, _ = open_session("120 m timber 45x95 C24\n45x95 C18 - 30 stk\n10 stk skruer 5x50\nblahblah ukendt ting\n45x95 timber\n5 stk fliser 30x30")
        t0 = time.perf_counter()
        v = call("POST", f"/sessions/{sid}/analyze")[1]
        ms = (time.perf_counter() - t0) * 1000
        L = {l["line_no"]: l for l in v["lines"]}
        check("FR-012 120 m / 4.8 = 25 pieces", L[1]["conversion"]["selling_quantity"] == 25 and "4.8" in L[1]["conversion"]["formula"])
        check("FR-008 C18 is never matched as C24", L[2]["final_sku"] != "SKU-DK-4595-480", L[2]["final_sku"])
        check("FR-007 items outside the catalog get no suggestion", not L[3]["match"]["candidates"] and not L[4]["match"]["candidates"],
              [L[3]["match"]["candidates"], L[4]["match"]["candidates"]])
        check("FR-009 missing grade never reaches the high band", L[5]["match"]["band"] != "HIGH", L[5]["match"]["band"])
        check("FR-010 blockers stop Confirm and name the lines", (lambda r: r[0] == 409 and err_code(r) == "UNRESOLVED_LINES"
                                                                  and r[1]["error"]["details"]["line_nos"])(confirm(sid)))
        known = [l for l in v["lines"] if l["stock"]["status"] not in (None, "UNKNOWN")]  # stock is evaluated once a quantity exists
        check("FR-014 every stock reading carries the reference label and its timestamp",
              known and all(l["stock"].get("label") and l["stock"].get("updated_at") for l in known) and all(l["stock"].get("label") for l in v["lines"]))

        # ---- substitution (FR-015/016/039)
        sid, _, _ = open_session("10 plader gips vådrum 12.5 mm")
        call("POST", f"/sessions/{sid}/analyze")
        call("PUT", f"/sessions/{sid}/lines/1/selection", {"sku": "SKU-GYP-MR-125", "decision": "SKU_EDITED"})
        alts = call("GET", f"/sessions/{sid}/lines/1/alternatives")[1]
        check("FR-015 only the safe alternative is offered", [a["sku"] for a in alts["items"]] == ["SKU-GYP-MR-125-B"], alts.get("items"))
        check("FR-016 reject needs a reason", err_code(call("PUT", f"/sessions/{sid}/lines/1/selection", {"sku": "SKU-GYP-MR-125", "decision": "SUBSTITUTION_REJECTED"})) == "REASON_REQUIRED")
        check("FR-016 SKU unchanged before the customer agrees", view(sid)["lines"][0]["final_sku"] == "SKU-GYP-MR-125")
        call("PUT", f"/sessions/{sid}/lines/1/selection", {"sku": "SKU-GYP-MR-125-B", "decision": "SUBSTITUTION_ACCEPTED"})
        r = confirm(sid)
        item = (r[1].get("payload") or {}).get("line_items", [{}])[0]
        check("FR-020 payload: original_sku kept, score null, substituted", item.get("original_sku") == "SKU-GYP-MR-125"
              and item.get("confidence_score") is None and item.get("fulfillment_action") == "substituted", item)

        # ---- confirm, idempotency, lock (FR-018/019/037)
        sid, _, _ = open_session(ORDER)
        call("POST", f"/sessions/{sid}/analyze")
        resolve_all(sid)
        c1 = confirm(sid)[1]
        c2 = confirm(sid)[1]
        check("FR-019 Confirm -> POS_ACCEPTED with reference", c1.get("order_status") == "POS_ACCEPTED" and str(c1.get("fulfillment_reference", "")).startswith("POS-"), c1.get("order_status"))
        check("FR-018 repeat Confirm replays the same reference", c2.get("replayed") is True and c2.get("fulfillment_reference") == c1.get("fulfillment_reference"))
        wrong_key = confirm(sid, key="different-key")
        missing_key = call("POST", f"/sessions/{sid}/confirm", {})
        check("FR-018 different key on replay -> 409 IDEMPOTENCY_CONFLICT", wrong_key[0] == 409 and err_code(wrong_key) == "IDEMPOTENCY_CONFLICT")
        check("FR-018 missing key -> 422", missing_key[0] == 422 and err_code(missing_key) == "VALIDATION")
        check("FR-018 confirmed order is read-only", err_code(call("PATCH", f"/sessions/{sid}/lines/1", {"requested_qty": 999})) == "SESSION_LOCKED")
        check("SRS 7 confirm response has order_session_id/locked/delivery_status", all(k in c1 for k in ("order_session_id", "locked", "delivery_status")))

        # ---- store dictionary and simulated sign-in (FR-021/032)
        st, d = call("GET", "/store-dictionary")
        check("FR-021 store dictionary endpoint is available", st == 200 and "items" in d, st)
        check("FR-021 removing an unknown mapping is a clean 404", err_code(call("DELETE", "/store-dictionary/999999")) == "NOT_FOUND")
        lg = call("POST", "/auth/login", {"username": "EMP-1042", "password": "definitely-wrong"})
        check("FR-032 login answers 401/503 with the standard envelope (never a 500)", lg[0] in (401, 503) and err_code(lg) in ("INVALID_CREDENTIALS", "LOGIN_DISABLED"), lg[0])

        # ---- fail modes: the counter never stops (FR-003/033, NFR-006)
        for label, ai, pos, expect in (("AI off", True, False, "POS_ACCEPTED"), ("POS off", False, True, "NEEDS_MANUAL"), ("AI+POS off", True, True, "NEEDS_MANUAL")):
            call("POST", "/admin/fail-modes", {"ai": ai, "pos": pos})
            sid, _, _ = open_session(ORDER + "\n45x95 timber")
            va = call("POST", f"/sessions/{sid}/analyze")[1]
            resolve_all(sid)
            r = confirm(sid)[1]
            ok = r.get("order_status") == expect and (not ai or va.get("ai_degraded") is True)
            if expect == "NEEDS_MANUAL":
                csv = call_text(f"/sessions/{sid}/export.csv")
                ok = ok and csv[1].startswith("﻿order_session_id;") and str(r.get("fulfillment_reference", "")).startswith("CSV-")
            check(f"NFR-006 {label}: staff still finish the order -> {expect}", ok, r.get("order_status"))
        call("POST", "/admin/fail-modes", {"ai": False, "pos": False})

        # ---- performance (NFR-003): 20 lines, warm
        twenty = "\n".join(["120 m timber 45x95 C24", "5 poser cement 25 kg", "12 skivor gips 12.5 mm", "10 x 4.8m timber 45x95 C24", "20 pakker isolering 95 mm"] * 4)
        times = []
        for _ in range(6):
            sid, _, _ = open_session(twenty)
            t0 = time.perf_counter()
            call("POST", f"/sessions/{sid}/analyze")
            times.append((time.perf_counter() - t0) * 1000)
        times = sorted(times[1:])  # first run is warm-up
        check("NFR-003 20-line analyze p50 <= 3000 ms (warm)", times[len(times) // 2] <= 3000, f"p50={times[len(times)//2]:.0f} ms, max={times[-1]:.0f} ms")
    except Exception as e:  # noqa: BLE001 - report what was reached instead of dying silently
        check(f"script error after {len(RESULTS)} checks", False, f"{type(e).__name__}: {e}")
    finally:
        call("POST", "/admin/fail-modes", {"ai": False, "pos": False})

    width = max(len(r[0]) for r in RESULTS)
    for label, ok, detail in RESULTS:
        print(f"{'PASS' if ok else 'FAIL'}  {label.ljust(width)}  {'' if ok else detail}")
    failed = [r for r in RESULTS if not r[1]]
    print(f"\n{len(RESULTS) - len(failed)}/{len(RESULTS)} checks passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
