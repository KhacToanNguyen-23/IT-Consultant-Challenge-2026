"use client";

import { useRouter } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";
import clsx from "clsx";
import { AlertTriangle, CheckCircle2, Download, FileText, FilePlus2, FileSignature, ListChecks, ScanLine, Search, UserRound } from "lucide-react";
import { api, ApiError, fileUrl, fmtMoney, type Customer, type SessionView } from "@/client/api";
import { useI18n } from "@/client/i18n";
import LinePanel from "@/components/pos/LinePanel";
import { LoadingTerminal, Notice, PosKey, SoftKeys, Terminal, Vfd } from "@/components/pos/Terminal";
import TicketLines, { lineAmount } from "@/components/pos/TicketLines";
import ListPagination from "@/components/pos/ListPagination";
import { StatePill } from "@/components/StatusBadge";

import ResultStory from "@/components/story/ResultStory";


const BLOCKER_PAGE_SIZE = 5;

function plusDays(n: number) {
  const d = new Date();
  d.setDate(d.getDate() + n);
  return d.toISOString().slice(0, 10);
}

export default function SessionPage({ params }: { params: { id: string } }) {
  const router = useRouter();
  const { t, lang } = useI18n();
  const [s, setS] = useState<SessionView | null>(null);
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [clientId, setClientId] = useState("");
  const [validUntil, setValidUntil] = useState(plusDays(7));
  const [sourceOpen, setSourceOpen] = useState<boolean | null>(null);
  const [selected, setSelected] = useState<number | null>(null);
  const [blockerPage, setBlockerPage] = useState(0);
  const opened = useRef(false);

  const load = useCallback(async () => {
    try {
      const v = await api<SessionView>(`/sessions/${params.id}`);
      setS(v);
      setClientId((c) => c || v.client_id || "");
      if (!opened.current) {
        opened.current = true;
        if (v.analyzed && !v.locked) setSelected(v.blockers[0]?.line_no ?? v.lines.find((l) => !l.final_sku || l.match.band !== "HIGH")?.line_no ?? v.lines[0]?.line_no ?? null);
      }
    } catch (e) {
      setError(e instanceof ApiError ? e.message : String(e));
    }
  }, [params.id]);

  // reload on language change: blockers, stock labels and reasons come translated from the API
  useEffect(() => {
    load();
    api<{ items: Customer[] }>("/customers").then((r) => setCustomers(r.items)).catch(() => {});
    const h = () => load();
    window.addEventListener("sitedesk:health", h);
    return () => window.removeEventListener("sitedesk:health", h);
  }, [load, lang]);
  useEffect(() => setBlockerPage((page) => Math.min(page, Math.max(0, Math.ceil((s?.blockers.length ?? 0) / BLOCKER_PAGE_SIZE) - 1))), [s?.blockers.length]);

  const act = async (key: string, fn: () => Promise<void>) => {
    setBusy(key);
    setError(null);
    try {
      await fn();
    } catch (e) {
      if (e instanceof ApiError) {
        const lines = (e.details?.line_nos as number[] | undefined)?.join(", ");
        setError(e.message + (lines ? ` (${t("line_n", { n: lines })})` : ""));
      } else setError(String(e));
    } finally {
      setBusy(null);
    }
  };

  if (!s) return <LoadingTerminal error={error} />;

  const isEmail = s.input_type === "email";
  const walkIn = customers.find((c) => c.customer_type === "B2C_WalkIn")?.client_id;
  const effectiveClient = clientId || walkIn || "";
  const canConfirmQuote = !s.quote || s.quote.status === "PREPARING";
  const line = s.lines.find((l) => l.line_no === selected) || null;
  const blockerNos = s.blockers.map((b) => b.line_no);
  const showSource = sourceOpen ?? !s.analyzed;

  const amounts = s.lines.map(lineAmount);
  const total = amounts.reduce<number>((sum, a) => sum + (a ?? 0), 0);
  const unpriced = amounts.filter((a) => a == null).length;
  const currency = s.lines.find((l) => l.currency)?.currency || "DKK";
  const matchedCount = s.lines.filter((l) => !!l.final_sku).length;
  const stockAlertCount = s.lines.filter((l) => l.stock.status === "PARTIAL" || l.stock.status === "OUT_OF_STOCK").length;
  const manualLine = s.blockers[0]?.line_no ?? s.lines.find((l) => !l.final_sku)?.line_no ?? s.lines[0]?.line_no ?? null;

  // A resolved line hands over to the next one, so the associate never hunts for what is left.
  const onLineChange = (v: SessionView) => {
    const wasBlocked = selected != null && blockerNos.includes(selected);
    const stillBlocked = v.blockers.some((b) => b.line_no === selected);
    setS(v);
    if (wasBlocked && !stillBlocked) setSelected(v.blockers[0]?.line_no ?? null);
  };

  const nextIssue = () => {
    const after = blockerNos.find((n) => selected == null || n > selected);
    setSelected(after ?? blockerNos[0] ?? null);
  };

  const analyze = () =>
    act("analyze", async () => {
      const v = await api<SessionView>(`/sessions/${s.session_id}/analyze`, { method: "POST", json: { language_hint: "DA" } });
      setS(v);
      setSelected(v.blockers[0]?.line_no ?? v.lines.find((l) => !l.final_sku || l.match.band !== "HIGH")?.line_no ?? v.lines[0]?.line_no ?? null);
    });

  const confirm = () =>
    act("confirm", async () => {
      await api(`/sessions/${s.session_id}/confirm`, { method: "POST", json: { client_id: effectiveClient }, headers: { "Idempotency-Key": s.order_session_id } });
      setSelected(null);
      await load();
    });

  const saveQuote = () =>
    act("quote", async () => {
      const q = await api<{ quote_id: string }>("/quotes", { method: "POST", json: { session_id: s.session_id, client_id: effectiveClient, valid_until: validUntil } });
      router.push(`/quotes/${q.quote_id}`);
    });

  const visibleBlockers = s.blockers.slice(blockerPage * BLOCKER_PAGE_SIZE, (blockerPage + 1) * BLOCKER_PAGE_SIZE);
  const vfdTop = s.locked ? s.confirmation.order_status || s.status : !s.analyzed ? t("vfd_review", { n: s.read_line_count }) : s.blockers.length ? t("vfd_blocked", { n: s.blockers.length }) : t("vfd_clear");

  return (
    <Terminal
      ticket={
        <div className="paper">
          <div className="paper-head">
            <div className="flex flex-wrap items-start gap-x-4 gap-y-2">
              <div className="min-w-0">
                <div className="text-sm soft">{isEmail ? t("flow2") : t("flow1")}</div>
                <h1 className="paper-title">
                  {s.order_session_id} <StatePill status={s.status} />
                </h1>
              </div>
            </div>
            <Stepper analyzed={s.analyzed} locked={s.locked} blockers={s.blockers.length} />
            {s.analyzed && (
              <div className="flow-summary" aria-label={t("review_summary")}>
                <FlowMetric label={t("metric_skus")} value={`${matchedCount}/${s.lines.length}`} />
                <FlowMetric label={t("metric_attention")} value={s.blockers.length} tone={s.blockers.length ? "warn" : "good"} />
                <FlowMetric label={t("metric_stock_alerts")} value={stockAlertCount} tone={stockAlertCount ? "warn" : "good"} />
              </div>
            )}

          </div>



          {(s.ai_degraded || s.lines.some((l) => l.stock.status === "UNKNOWN") || error) && (
            <div className="space-y-2 px-[18px] py-3">
              {s.ai_degraded && (
                <Notice tone="warn" icon={<AlertTriangle size={16} />}>
                  {t("ai_degraded_banner")}
                </Notice>
              )}
              {s.lines.some((l) => l.stock.status === "UNKNOWN") && (
                <Notice tone="warn" icon={<AlertTriangle size={16} />}>
                  {t("stock_unknown_banner")}
                </Notice>
              )}
              {error && (
                <Notice tone="bad" alert>
                  {error}
                </Notice>
              )}
            </div>
          )}

          {s.masked_source && showSource && (
            <div className="border-b-2 border-dashed border-[var(--rule)] px-[18px] py-3">
              <div className="mb-1 font-semibold">{t("source_title", { n: s.read_line_count })}</div>
              <pre className="font-mono max-h-48 overflow-auto whitespace-pre-wrap text-xs">{s.masked_source}</pre>
              <p className="mt-2 text-[11px] soft">{t("source_note")}</p>
            </div>
          )}

          <TicketLines session={s} selected={selected} onSelect={setSelected} />
          <p className="paper-foot">{t("table_foot")}</p>
        </div>
      }
      rail={
        <>
          <Vfd
            top={vfdTop}
            main={s.analyzed ? fmtMoney(total, "").trim() : s.read_line_count}
            unit={s.analyzed ? currency : undefined}
            sub={s.analyzed ? (unpriced ? `${t("vfd_list_total")}, ${t("vfd_unpriced", { n: unpriced })}` : t("vfd_list_total")) : undefined}
          />
          <div className="pos-screen">
            {s.analyzed && s.ai_degraded && !line && manualLine != null && (
              <PosKey tone="nav" icon={<Search size={17} />} onClick={() => setSelected(manualLine)} className="mb-3 w-full">
                {t("manual_fallback_action")}
              </PosKey>
            )}
            {line ? (
              <LinePanel key={line.line_id} session={s} line={line} onChange={onLineChange} onClose={() => setSelected(null)} />
            ) : s.locked ? (
              <ConfirmResult s={s} />
            ) : s.analyzed ? (
              <div className="space-y-3">
                <h2 className="screen-title">
                  {t("step4_title")} {s.quote && t("quote_ref", { id: s.quote.quote_id })}
                </h2>
                <div role="group" aria-label={t("client_id")}>
                  <div className="mb-1.5 font-semibold">{t("client_id")}</div>
                  <div className="grid grid-cols-2 gap-1.5">
                    {customers.map((c) => (
                      <button key={c.client_id} type="button" disabled={!!s.quote} aria-pressed={effectiveClient === c.client_id} onClick={() => setClientId(c.client_id)} className="tile">
                        <span className="block font-semibold leading-tight">{c.customer_type === "B2B" ? c.client_id : t("walk_in")}</span>
                        <span className="block break-all text-xs soft">{c.customer_type === "B2B" ? `B2B, ${c.discount_tier}` : c.client_id}</span>
                      </button>
                    ))}
                  </div>
                </div>

                {s.blockers.length > 0 && (
                  <div>
                    <div className="mb-1.5 font-semibold text-amber-900">{t("cannot_confirm", { n: s.blockers.length })}</div>
                    <ul className="space-y-1.5">
                      {visibleBlockers.map((b) => (
                        <li key={b.line_no}>
                          <button type="button" className="tile text-sm" onClick={() => setSelected(b.line_no)}>
                            <b>{t("line_n", { n: b.line_no })}:</b> {b.reason}
                          </button>
                        </li>
                      ))}
                    </ul>
                    <ListPagination total={s.blockers.length} page={blockerPage} pageSize={BLOCKER_PAGE_SIZE} onPageChange={setBlockerPage} />
                  </div>
                )}

                {!canConfirmQuote && <Notice tone="quote">{t("quote_needs_prepare", { id: s.quote!.quote_id, status: s.quote!.status })}</Notice>}
                {s.quote && (
                  <p>
                    {t("quote_n", { id: s.quote.quote_id })}: <StatePill status={s.quote.status} />
                  </p>
                )}

                {!s.quote && (
                  <div className="space-y-1.5">
                    <label className="block font-semibold">
                      {t("valid_until")}
                      <input type="date" value={validUntil} min={plusDays(0)} onChange={(e) => setValidUntil(e.target.value)} className="field mt-1 font-normal" />
                    </label>
                    <p className="screen-note">{t("save_quote_note")}</p>
                  </div>
                )}
                <p className="screen-note">{t("confirm_note")}</p>
              </div>
            ) : (
              <p className="screen-title">{t("step2_hint", { n: s.read_line_count })}</p>
            )}
          </div>
        </>
      }
      keys={
        <SoftKeys
          slots={[
            <PosKey key="new" hotkey="F3" icon={<FilePlus2 size={17} />} href="/">
              {t("new_list")}
            </PosKey>,
            s.masked_source ? (
              <PosKey key="src" hotkey="F4" icon={<FileText size={17} />} tone={showSource ? "on" : "std"} current={showSource} onClick={() => setSourceOpen(!showSource)}>
                {t("source")}
              </PosKey>
            ) : null,
            !s.locked && s.analyzed ? (
              <PosKey key="next" hotkey="F6" tone="hold" icon={<ListChecks size={17} />} disabled={!blockerNos.length} onClick={nextIssue}>
                {t("key_next_issue")} {blockerNos.length > 0 && `(${blockerNos.length})`}
              </PosKey>
            ) : null,
            !s.locked && s.analyzed ? (
              <PosKey key="cust" hotkey="F7" tone={line ? "std" : "on"} icon={<UserRound size={17} />} onClick={() => setSelected(null)}>
                {t("key_order")}
              </PosKey>
            ) : null,
            s.locked ? (
              s.confirmation.csv_download_url ? (
                <PosKey key="csv" hotkey="F8" tone="hold" icon={<Download size={17} />} href={fileUrl(s.confirmation.csv_download_url)} external>
                  {t("download_csv_short")}
                </PosKey>
              ) : null
            ) : !s.analyzed ? null : s.quote ? (
              <PosKey key="quote" hotkey="F8" tone="quote" icon={<FileSignature size={17} />} href={`/quotes/${s.quote.quote_id}`}>
                {t("open_quote")}
              </PosKey>
            ) : (
              <PosKey key="quote" hotkey="F8" tone="quote" icon={<FileSignature size={17} />} busy={busy === "quote"} disabled={!!busy || !effectiveClient} onClick={saveQuote}>
                {t("save_quote")}
              </PosKey>
            ),
            s.locked ? null : !s.analyzed ? (
              <PosKey key="analyze" hotkey="F9" tone="nav" icon={<ScanLine size={18} />} busy={busy === "analyze"} disabled={!!busy} onClick={analyze}>
                {t("analyze")}
              </PosKey>
            ) : (
              <PosKey key="confirm" hotkey="F9" tone="go" icon={<CheckCircle2 size={18} />} busy={busy === "confirm"} disabled={!!busy || s.blockers.length > 0 || !canConfirmQuote || !effectiveClient} onClick={confirm}>
                {t("confirm_send")}
              </PosKey>
            ),
          ]}
        />
      }
    />
  );
}

function Stepper({ analyzed, locked, blockers }: { analyzed: boolean; locked: boolean; blockers: number }) {
  const { t } = useI18n();
  const current = locked ? 3 : !analyzed ? 1 : blockers > 0 ? 2 : 3;
  const steps = [
    { label: t("step_received"), done: true },
    { label: t("step_read"), done: analyzed },
    { label: blockers ? `${t("step_review")} (${blockers})` : t("step_review"), done: analyzed && blockers === 0 },
    { label: t("step_confirm"), done: locked },
  ];
  return (
    <ol className="mt-2 flex flex-wrap items-center gap-x-4 gap-y-1 text-sm">
      {steps.map((st, i) => (
        <li key={i} aria-current={i === current ? "step" : undefined} className={clsx("flex items-center gap-1.5 rounded-full px-2 py-1", st.done ? "font-semibold" : "soft", i === current && "bg-blue-50 text-blue-950 ring-1 ring-blue-200")}>
          <span className={clsx("lamp", st.done && "lamp--ok")} aria-hidden />
          {i + 1}. {st.label}
        </li>
      ))}
    </ol>
  );
}

function FlowMetric({ label, value, tone = "default" }: { label: string; value: React.ReactNode; tone?: "default" | "warn" | "good" }) {
  return (
    <div className={clsx("flow-metric", tone === "warn" && "flow-metric--warn", tone === "good" && "flow-metric--good")}>
      <span className="flow-metric-value tabular">{value}</span>
      <span className="flow-metric-label">{label}</span>
    </div>
  );
}

function ConfirmResult({ s }: { s: SessionView }) {
  const { t } = useI18n();
  const c = s.confirmation;
  const ok = c.order_status === "POS_ACCEPTED";
  return (
    <div className="receipt">
      <div className="text-center text-base font-semibold">{ok ? t("pos_ok") : t("pos_csv")}</div>
      <div className="my-2 border-t-2 border-dashed border-[var(--rule)]" />
      <dl className="space-y-1.5">
        <div>
          <dt className="soft">{t("order_status")}</dt>
          <dd className="flex flex-wrap gap-1">
            <StatePill status={c.order_status || s.status} /> {!ok && <StatePill status="SENT_OR_EXPORTED" />}
          </dd>
        </div>
        <div>
          <dt className="soft">{t("reference")}</dt>
          <dd className="break-all font-semibold">{c.fulfillment_reference}</dd>
        </div>
        {c.pos_order_ref && (
          <div>
            <dt className="soft">POS order ref</dt>
            <dd className="break-all font-semibold">{c.pos_order_ref}</dd>
          </div>
        )}
        <div>
          <dt className="soft">{t("client")}</dt>
          <dd className="break-all font-semibold">{s.client_id}</dd>
        </div>
        {c.processing_time_seconds != null && (
          <div>
            <dt className="soft">{t("time_to_confirm")}</dt>
            <dd className="font-semibold tabular">{c.processing_time_seconds} s</dd>
          </div>
        )}
      </dl>
      <div className="my-2 border-t-2 border-dashed border-[var(--rule)]" />
      <p className="text-xs soft">{t("locked_note")}</p>
      <ResultStory session={s} />
    </div>
  );
}
