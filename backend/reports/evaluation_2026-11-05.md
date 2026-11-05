# SiteDesk — SKU matching evaluation (initial results on 98 lines)

Generated 2026-11-05T17:56:19+00:00 · labels human-reviewed: **0/98** · catalog 62 SKU (simulated)
Embedding: `local/intfloat/multilingual-e5-small` · thresholds high >0.9, review ≥0.8, gap 0.05
Hardware: Linux-6.6.114.1-microsoft-standard-WSL2-x86_64-with-glibc2.41, 16 CPU

> Fewer than 150 labelled lines: these are **initial results**, NFR-05 (high-band false match ≤2%) is NOT claimed as met.
> Labels were drafted with AI assistance; numbers are only quotable after a teammate reviews every row (`reviewed` flag).

| Metric | Embedding + hard rules | Rules-only fallback (AI fail) |
|---|---|---|
| Top-1 accuracy (answerable lines) | 1.0 | 0.987 |
| Correct SKU in top-3 | 1.0 | 1.0 |
| High-band coverage (zero-touch potential) | 0.797 | 0.797 |
| High band: wrong / count | 0/63 | 0/63 |
| High band error, Wilson 95% upper | 0.0575 | 0.0575 |
| Must-clarify lines correctly NOT auto-accepted | 19/19 | 19/19 |
| Trap lines where any SKU was offered (should be 0) | 0 | 0 |

## Embedding mode by band

| Band | Count | Correct | Error rate |
|---|---|---|---|
| HIGH | 63 | 63 | 0.0 |
| NONE | 11 | 11 | 0.0 |
| REVIEW | 24 | 24 | 0.0 |

## By language (embedding mode)

| Lang | n | Correct | Wrong-high |
|---|---|---|---|
| DA | 66 | 66 | 0 |
| EN | 10 | 10 | 0 |
| NO | 12 | 12 | 0 |
| SV | 10 | 10 | 0 |

## By case type (embedding mode)

- **easy**: 36/36
- **missing**: 8/8
- **other_lang**: 28/28
- **slang**: 15/15
- **trap**: 11/11

## Performance — analyze 20 lines (NFR-003 target ≤3.0 s after warm-up)

20 runs, mode `embedding`: p50 **200.9 ms**, p95 **297.9 ms**, max 305.2 ms.
Stage p50: {'embed_ms': 104.6, 'vector_ms': 30.0, 'stock_ms': 17.7, 'rules_convert_alternatives_ms': 0.7}. External LLM not used in the matching path.

## Misses in embedding mode (0)

| id | text | kind | expected | got | band |
|---|---|---|---|---|---|
