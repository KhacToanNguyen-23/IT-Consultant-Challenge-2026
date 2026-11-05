-- SiteDesk KPI queries (SRS v2 section 10, MVP-FR-031). Seed/demo numbers are simulated, never real-store evidence.
-- Each block starts with "-- name: <id>"; scripts/kpi.py and the tests run them one by one.

-- name: time_to_serve
-- Seconds from "valid upload/text accepted" (processing_started_at) to Confirm.
SELECT count(*) AS confirmed_sessions,
       percentile_cont(.5) WITHIN GROUP (ORDER BY EXTRACT(EPOCH FROM (confirmed_at - processing_started_at))) AS median_seconds,
       avg(EXTRACT(EPOCH FROM (confirmed_at - processing_started_at))) AS avg_seconds,
       count(*) FILTER (WHERE confirmed_at - processing_started_at < interval '120 seconds')::numeric / NULLIF(count(*), 0) AS under_2m_rate
FROM order_sessions
WHERE confirmed_at IS NOT NULL AND processing_started_at IS NOT NULL;

-- name: substitution_acceptance
-- accepted / all stock-out-or-partial lines of confirmed sessions (Round 1 denominator).
WITH eligible AS (
  SELECT sl.line_id FROM session_lines sl JOIN order_sessions s USING (session_id)
  WHERE s.confirmed_at IS NOT NULL AND sl.stock_status IN ('PARTIAL', 'OUT_OF_STOCK')
), accepted AS (
  SELECT DISTINCT line_id FROM decision_events WHERE event_type = 'SUBSTITUTION_ACCEPTED'
), offered AS (
  SELECT DISTINCT line_id FROM decision_events WHERE event_type = 'AI_SUGGESTED' AND metadata->>'suggestion_type' = 'alternative'
)
SELECT count(a.line_id) AS accepted,
       count(e.line_id) AS total_stockouts,
       count(a.line_id)::numeric / NULLIF(count(e.line_id), 0) AS acceptance_rate,
       count(o.line_id)::numeric / NULLIF(count(e.line_id), 0) AS offered_rate
FROM eligible e LEFT JOIN accepted a USING (line_id) LEFT JOIN offered o USING (line_id);

-- name: zero_touch
-- Lines confirmed with match score > 0.90 and no associate edit (event-based; associate_edited is only a cache).
WITH touched AS (
  SELECT DISTINCT line_id FROM decision_events
  WHERE event_type IN ('PARSE_EDITED', 'SKU_EDITED', 'SUBSTITUTION_ACCEPTED', 'SUBSTITUTION_REJECTED')
), eligible_lines AS (
  SELECT sl.* FROM session_lines sl JOIN order_sessions s USING (session_id)
  WHERE s.confirmed_at IS NOT NULL AND sl.resolved = true AND sl.manually_added = false
)
SELECT count(*) FILTER (WHERE el.match_score > .90 AND t.line_id IS NULL) AS zero_touch_lines,
       count(*) AS confirmed_lines,
       count(*) FILTER (WHERE el.match_score > .90 AND t.line_id IS NULL)::numeric / NULLIF(count(*), 0) AS zero_touch_rate
FROM eligible_lines el LEFT JOIN touched t ON t.line_id = el.line_id;
