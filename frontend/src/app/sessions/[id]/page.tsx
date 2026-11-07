"use client";

import { useRouter } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";
import { AlertTriangle, CheckCircle2, Download, FileText, FilePlus2, FileSignature, ListChecks, ScanLine, Search, ShieldCheck, UserRound } from "lucide-react";
import { api, ApiError, fileUrl, fmtMoney, fmtTime, type Customer, type SessionView } from "@/client/api";
import { useI18n } from "@/client/i18n";
import LinePanel from "@/components/pos/LinePanel";
import { LoadingTerminal, Notice, PosKey, SoftKeys, Terminal, Vfd } from "@/components/pos/Terminal";
import TicketLines, { lineAmount } from "@/components/pos/TicketLines";
import ListPagination from "@/components/pos/ListPagination";
import { StatePill } from "@/components/StatusBadge";
import ImpactStrip from "@/components/story/ImpactStrip";
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
  const llmCalls = Number(s.stage_timings_ms.llm_calls || 0);
  const stockChecked = s.lines.map((l) => l.stock.updated_at).filter(Boolean).sort().pop() || null;
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
                <h1 className="paper-title">
                  {s.order_session_id} <StatePill status={s.status} />
                </h1>
              </div>
            </div>
          </div>

          <div className="operation-proof" role="group" aria-label={t("evidence_title")}>
            <ProofTag tone="good" icon={<ShieldCheck size={14} aria-hidden />}>{t("evidence_masked")}</ProofTag>
            {s.analyzed && <ProofTag>{s.ai_degraded ? t("evidence_fallback") : t("evidence_semantic")}</ProofTag>}
            {s.analyzed && stockChecked && <ProofTag>{t("evidence_stock_checked", { time: fmtTime(stockChecked) })}</ProofTag>}
            {s.analyzed && llmCalls > 0 && <ProofTag>{t("evidence_llm", { n: llmCalls })}</ProofTag>}
          </div>

          {s.analyzed && (
            <div className="px-[18px] pt-2">
              <ImpactStrip session={s} />
            </div>
          )}

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
              <details className="source-limits mt-2">
                <summary>{t("source_limit_title")}</summary>
                <p className="mt-1 text-[11px] soft">{t("source_note")}</p>
              </details>
            </div>
          )}

          <TicketLines session={s} selected={selected} onSelect={setSelected} />
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
            {s.analyzed && !s.locked && s.ai_degraded && !line && manualLine != null && (
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
                {s.quote && <h2 className="screen-title">{t("quote_ref", { id: s.quote.quote_id })}</h2>}
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

                {!s.quote && s.input_type === "email" && (
                  <div className="space-y-1.5">
                    <label className="block font-semibold">
                      {t("valid_until")}
                      <input type="date" value={validUntil} min={plusDays(0)} onChange={(e) => setValidUntil(e.target.value)} className="field mt-1 font-normal" />
                    </label>
                  </div>
                )}
              </div>
            ) : null}
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
            s.locked ? null : !s.analyzed ? null : s.quote ? (
              <PosKey key="quote" hotkey="F8" tone="quote" icon={<FileSignature size={17} />} href={`/quotes/${s.quote.quote_id}`}>
                {t("open_quote")}
              </PosKey>
            ) : s.input_type === "email" ? (
              <PosKey key="quote" hotkey="F8" tone="quote" icon={<FileSignature size={17} />} busy={busy === "quote"} disabled={!!busy || !effectiveClient} onClick={saveQuote}>
                {t("save_quote")}
              </PosKey>
            ) : null,
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

function ConfirmResult({ s }: { s: SessionView }) {
  const { t } = useI18n();
  const c = s.confirmation;
  const ok = c.order_status === "POS_ACCEPTED";
  return (
    <div className="receipt">
      <div className="text-center text-base font-semibold">{ok ? t("pos_ok") : t("pos_csv")}</div>
      <div className="my-2 border-t-2 border-dashed border-[var(--rule)]" />
      {!ok && c.csv_download_url && (
        <PosKey hotkey="F8" size="sm" tone="hold" icon={<Download size={16} />} href={fileUrl(c.csv_download_url)} external className="mb-3 w-full">
          {t("download_csv_short")}
        </PosKey>
      )}
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
            <dt className="soft">{t("pos_order_ref")}</dt>
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
      <ResultStory session={s} />
    </div>
  );
}

function ProofTag({ children, icon, tone = "neutral" }: { children: React.ReactNode; icon?: React.ReactNode; tone?: "neutral" | "good" | "warn" }) {
  return <span className={`proof-tag proof-tag--${tone}`}>{icon}{children}</span>;
}
