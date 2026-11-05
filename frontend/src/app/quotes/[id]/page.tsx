"use client";

import { useCallback, useEffect, useState } from "react";
import clsx from "clsx";
import { AlertTriangle, Ban, CheckCircle2, ClipboardList, Download, FileSearch, List, PenLine, Printer, RefreshCw, Send, Wrench } from "lucide-react";
import { api, ApiError, API_URL, fileUrl, fmtMoney, fmtTime, type QuoteView } from "@/client/api";
import { useI18n, type Key } from "@/client/i18n";
import { LoadingTerminal, Notice, PosKey, SoftKeys, Terminal, useArmed, Vfd } from "@/components/pos/Terminal";
import { StatePill } from "@/components/StatusBadge";

const FLOW = ["SAVED", "SENT", "CUST", "PREPARING", "CONFIRMED"] as const;
const CHANNELS = [
  { id: "email", label: "ch_email" },
  { id: "phone", label: "ch_phone" },
  { id: "in_store", label: "ch_in_store" },
] as const;

export default function QuoteDetailPage({ params }: { params: { id: string } }) {
  const { t, lang } = useI18n();
  const [q, setQ] = useState<QuoteView | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [channel, setChannel] = useState("email");
  const [notice, setNotice] = useState<string | null>(null);
  const cancelKey = useArmed();

  const load = useCallback(async () => {
    try {
      setQ(await api<QuoteView>(`/quotes/${params.id}`));
    } catch (e) {
      setError(e instanceof ApiError ? e.message : String(e));
    }
  }, [params.id]);

  useEffect(() => {
    load();
  }, [load, lang]);

  const act = async (key: string, fn: () => Promise<QuoteView | void>, msg?: string) => {
    setBusy(key);
    setError(null);
    setNotice(null);
    try {
      const r = await fn();
      if (r) setQ(r);
      else await load();
      if (msg) setNotice(msg);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : String(e));
    } finally {
      setBusy(null);
    }
  };

  if (!q) return <LoadingTerminal error={error} />;

  const printUrl = (kind: string) => `${API_URL}/api/v1/quotes/${q.quote_id}/print?kind=${kind}&lang=${lang}`;
  const can = (a: string) => q.allowed_actions.includes(a);
  const reached = (k: (typeof FLOW)[number]) => {
    if (k === "CUST") return !!q.customer_confirmed_at;
    const order = ["SAVED", "SENT", "PREPARING", "CONFIRMED"];
    return order.indexOf(q.status) >= order.indexOf(k) || (k === "SENT" && !!q.customer_confirmed_at && q.status !== "SAVED");
  };
  const changedCount = q.lines.filter((l) => l.changed_fields.length).length;
  const shortCount = q.lines.filter((l) => l.alternative_required).length;
  const blockers = q.lines.filter((l) => l.current_line?.line_status === "SUBSTITUTE_PROPOSED" || l.current_line?.line_status === "NEEDS_CLARIFICATION").length;

  const cancel = () => {
    if (!cancelKey.armed) return cancelKey.arm();
    cancelKey.disarm();
    act("cancel", () => api(`/quotes/${q.quote_id}/transitions`, { method: "POST", json: { to_status: "CANCELLED" } }).then(() => undefined), t("cancelled_msg"));
  };

  const send = () => act("send", () => api(`/quotes/${q.quote_id}/transitions`, { method: "POST", json: { to_status: "SENT" } }).then(() => undefined), t("marked_sent"));
  const record = () => act("cust", () => api(`/quotes/${q.quote_id}/customer-confirmation`, { method: "POST", json: { channel } }), t("recorded"));
  const prepare = () => act("prepare", () => api<QuoteView>(`/quotes/${q.quote_id}/prepare`, { method: "POST" }), t("prepared"));
  const confirm = () => act("confirm", () => api(`/quotes/${q.quote_id}/confirm`, { method: "POST" }).then(() => undefined), t("confirmed_via_connector"));

  // F8 is the step before the main action, F9 the main action, whatever state the quote is in.
  const secondary = can("SEND") ? (
    <PosKey key="send" hotkey="F8" tone="quote" icon={<Send size={17} />} busy={busy === "send"} disabled={!!busy} onClick={send}>
      {t("key_send")}
    </PosKey>
  ) : can("PRINT_PICK_SLIP") ? (
    <PosKey key="pick" hotkey="F8" icon={<ClipboardList size={17} />} href={printUrl("pick-slip")} external>
      {t("key_pick")}
    </PosKey>
  ) : q.status === "CONFIRMED" && q.order.csv_download_url ? (
    <PosKey key="csv" hotkey="F8" tone="hold" icon={<Download size={17} />} href={fileUrl(q.order.csv_download_url)} external>
      {t("download_csv_short")}
    </PosKey>
  ) : null;

  const primary = can("RECORD_CUSTOMER_CONFIRMATION") ? (
    <PosKey key="rec" hotkey="F9" tone="quote" icon={<PenLine size={17} />} busy={busy === "cust"} disabled={!!busy} onClick={record}>
      {t("key_record")}
    </PosKey>
  ) : can("PREPARE") ? (
    <PosKey key="prep" hotkey="F9" tone="quote" icon={<RefreshCw size={17} />} busy={busy === "prepare"} disabled={!!busy} onClick={prepare}>
      {t("prepare")}
    </PosKey>
  ) : can("CONFIRM") ? (
    blockers > 0 ? (
      <PosKey key="res" hotkey="F9" tone="hold" icon={<AlertTriangle size={17} />} href={`/sessions/${q.session_id}`}>
        {t("resolve_short", { n: blockers })}
      </PosKey>
    ) : (
      <PosKey key="conf" hotkey="F9" tone="go" icon={<CheckCircle2 size={18} />} busy={busy === "confirm"} disabled={!!busy} onClick={confirm}>
        {t("confirm_send")}
      </PosKey>
    )
  ) : null;

  return (
    <Terminal
      ticket={
        <div className="paper">
          <div className="paper-head">
            <div className="text-sm soft">{t("flow2_short")}</div>
            <h1 className="paper-title">
              {q.quote_id} <StatePill status={q.status} />
            </h1>
            <dl className="mt-2 grid grid-cols-2 gap-x-4 gap-y-1.5 text-sm sm:grid-cols-3">
              <Info k="Client ID" v={`${q.client_id}${q.customer_type ? `, ${q.customer_type}` : ""}`} />
              <Info k={t("valid_until")} v={q.valid_until} />
              <Info k={t("discount")} v={`${q.applied_discount_tier} (${(q.discount_rate * 100).toFixed(0)}%)`} />
              <Info k={t("price_source")} v={q.price_source} />
              <Info k={t("price_time")} v={fmtTime(q.price_captured_at)} />
            </dl>
          </div>

          <div className="space-y-2 px-[18px] pt-3">
            <Notice tone="warn">
              <b>{q.disclaimer}</b>
            </Notice>
            {(q.status === "EXPIRED" || q.status === "CANCELLED") && (
              <Notice tone="bad" icon={<Ban size={16} />}>
                <b>
                  {q.status === "EXPIRED" ? t("expired_banner", { date: q.valid_until }) : t("cancelled_banner")} {t("cannot_confirm_short")}
                </b>
              </Notice>
            )}
            {q.live_error && (
              <Notice tone="warn" icon={<AlertTriangle size={16} />}>
                {q.live_error}
              </Notice>
            )}
          </div>

          <div className="flex flex-wrap items-center gap-x-3 gap-y-1 px-[18px] pb-1 pt-3">
            <span className="font-semibold">{t("snap_vs_live")}</span>
            {q.live_checked_at && <span className="text-xs soft">{t("checked_at", { time: fmtTime(q.live_checked_at) })}</span>}
            {changedCount > 0 && <span className="rounded bg-amber-100 px-2 py-0.5 text-xs font-semibold text-amber-900">{t("n_changed", { n: changedCount })}</span>}
            {shortCount > 0 && <span className="rounded bg-red-100 px-2 py-0.5 text-xs font-semibold text-red-900">{t("n_short", { n: shortCount })}</span>}
          </div>

          <div className="overflow-x-auto">
            <table className="w-full min-w-[640px] text-sm">
              <thead className="border-y border-[var(--ink)] text-left font-[family-name:var(--font-key)] text-sm soft">
                <tr>
                  <th className="px-[18px] py-1.5 font-semibold">#</th>
                  <th className="px-2 py-1.5 font-semibold">{t("col_sku_product")}</th>
                  <th className="px-2 py-1.5 font-semibold">{t("col_qty_short")}</th>
                  <th className="px-2 py-1.5 font-semibold">{t("col_net_price")}</th>
                  <th className="px-2 py-1.5 font-semibold">{t("col_stock")}</th>
                  <th className="px-2 py-1.5 pr-[18px] font-semibold">{t("col_current_line")}</th>
                </tr>
              </thead>
              <tbody>
                {q.lines.map((l) => {
                  const priceChanged = l.changed_fields.includes("price");
                  const stockChanged = l.changed_fields.includes("stock");
                  return (
                    <tr key={l.line_no} className={clsx("border-b border-dotted border-[var(--rule)] align-top", (priceChanged || stockChanged) && "bg-amber-50", l.alternative_required && "bg-red-50")}>
                      <td className="font-mono px-[18px] py-2 soft tabular">{l.line_no}</td>
                      <td className="px-2 py-2">
                        <div className="text-[15px] font-semibold leading-snug">{l.name}</div>
                        <div className="font-mono text-xs soft">{l.sku}</div>
                        <div className="font-mono text-xs soft">“{l.raw_customer_input}”</div>
                      </td>
                      <td className="px-2 py-2 tabular">
                        {l.quantity} × {l.selling_unit}
                      </td>
                      <td className="font-mono px-2 py-2 tabular">
                        <Diff before={fmtMoney(l.snapshot.unit_price, q.currency)} after={l.live ? fmtMoney(l.live.unit_price, q.currency) : null} changed={priceChanged} />
                      </td>
                      <td className="font-mono px-2 py-2 tabular">
                        <Diff before={String(l.snapshot.on_hand)} after={l.live?.on_hand != null ? String(l.live.on_hand) : null} changed={stockChanged} />
                        {l.alternative_required && <div className="mt-1 font-sans text-xs font-semibold text-red-900">{t("short_alt")}</div>}
                      </td>
                      <td className="px-2 py-2 pr-[18px] text-xs">
                        {l.current_line && (
                          <>
                            <div>{t(`ls_${l.current_line.line_status}` as Key)}</div>
                            {l.current_line.final_sku !== l.sku && <div className="text-emerald-800">→ {l.current_line.final_sku}</div>}
                            {l.current_line.fulfillment_action && <div className="soft">{l.current_line.fulfillment_action}</div>}
                          </>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          <p className="paper-foot !border-t-0">{t("quote_foot")}</p>
        </div>
      }
      rail={
        <>
          <Vfd top={q.status} main={fmtMoney(q.snapshot_total, "").trim()} unit={q.currency} sub={t("vfd_quote_total")} />
          <div className="pos-screen space-y-3">
            <ol className="grid gap-1" aria-label={t("flow_steps")}>
              {FLOW.map((k) => (
                <li key={k} className={clsx("flex items-center gap-2", reached(k) ? "font-semibold" : "soft")}>
                  <span className={clsx("lamp", reached(k) && "lamp--ok")} aria-hidden />
                  {t(`qf_${k}` as Key)}
                </li>
              ))}
            </ol>

            {error && (
              <Notice tone="bad" alert>
                {error}
              </Notice>
            )}
            {notice && <Notice tone="good">{notice}</Notice>}

            {can("RECORD_CUSTOMER_CONFIRMATION") && (
              <div role="group" aria-label={t("cust_conf_via")}>
                <div className="mb-1.5 font-semibold">{t("cust_conf_via")}</div>
                <div className="grid grid-cols-3 gap-1.5">
                  {CHANNELS.map((c) => (
                    <button key={c.id} type="button" aria-pressed={channel === c.id} onClick={() => setChannel(c.id)} className="tile text-center font-semibold">
                      {t(c.label)}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {q.customer_confirmed_at && <p className="text-sm font-semibold text-emerald-900">{t("cust_confirmed_at", { time: fmtTime(q.customer_confirmed_at), by: q.customer_confirmed_by || "" })}</p>}
            {!q.customer_confirmed_at && ["SAVED", "SENT"].includes(q.status) && <p className="screen-note">{t("prepare_locked")}</p>}

            {q.status === "CONFIRMED" && (
              <Notice tone={q.order.pos_order_ref ? "good" : "warn"}>
                {q.order.pos_order_ref ? t("pos_received") : t("pos_failed_csv")} <b className="font-mono break-all">{q.order.pos_order_ref || q.order.fulfillment_reference}</b>
              </Notice>
            )}

            <button type="button" className="tile inline-flex items-center gap-2 font-semibold" disabled={!!busy} onClick={() => act("reload", async () => {}, t("rechecked"))}>
              <RefreshCw size={15} aria-hidden /> {t("recheck")}
            </button>

            {["SAVED", "SENT", "PREPARING"].includes(q.status) && <DemoTools q={q} onDone={load} />}
          </div>
        </>
      }
      keys={
        <SoftKeys
          slots={[
            <PosKey key="back" hotkey="F3" icon={<List size={17} />} href="/quotes">
              {t("back_quotes")}
            </PosKey>,
            <PosKey key="print" hotkey="F4" icon={<Printer size={17} />} href={printUrl("quote")} external>
              {t("key_print")}
            </PosKey>,
            <PosKey key="review" hotkey="F6" icon={<FileSearch size={17} />} href={`/sessions/${q.session_id}`}>
              {t("key_review")}
            </PosKey>,
            can("CANCEL") ? (
              <PosKey key="cancel" hotkey="F7" tone="void" icon={<Ban size={17} />} busy={busy === "cancel"} disabled={!!busy} onClick={cancel}>
                {cancelKey.armed ? t("key_again") : t("cancel_quote")}
              </PosKey>
            ) : null,
            secondary,
            primary,
          ]}
        />
      }
    />
  );
}

function Info({ k, v }: { k: string; v: string }) {
  return (
    <div className="min-w-0">
      <dt className="text-xs soft">{k}</dt>
      <dd className="break-words font-semibold">{v}</dd>
    </div>
  );
}

function Diff({ before, after, changed }: { before: string; after: string | null; changed: boolean }) {
  if (!after || !changed) return <span>{before}</span>;
  return (
    <span>
      <span className="soft line-through">{before}</span> <span className="font-semibold text-amber-900">→ {after}</span>
    </span>
  );
}

/** Demo only: change simulated POS price/stock to show the reopen diff (MVP-FR-025). */
function DemoTools({ q, onDone }: { q: QuoteView; onDone: () => void }) {
  const { t } = useI18n();
  const [sku, setSku] = useState(q.lines[0]?.sku || "");
  const [price, setPrice] = useState("");
  const [stock, setStock] = useState("");
  const [msg, setMsg] = useState<string | null>(null);
  const skus = Array.from(new Set(q.lines.map((l) => l.sku)));
  return (
    <details className="rounded border border-dashed border-[#8f9591] p-2 text-sm">
      <summary className="flex cursor-pointer items-center gap-2 font-semibold">
        <Wrench size={14} aria-hidden /> {t("demo_tools")}
      </summary>
      <div className="mt-2 space-y-2">
        <select value={sku} onChange={(e) => setSku(e.target.value)} aria-label="SKU" className="field">
          {skus.map((s) => (
            <option key={s}>{s}</option>
          ))}
        </select>
        <div className="grid grid-cols-2 gap-2">
          <input value={price} onChange={(e) => setPrice(e.target.value)} placeholder={t("new_list_price")} aria-label={t("new_list_price")} inputMode="decimal" className="field" />
          <input value={stock} onChange={(e) => setStock(e.target.value)} placeholder={t("new_stock")} aria-label={t("new_stock")} inputMode="decimal" className="field" />
        </div>
        <div className="grid grid-cols-2 gap-2">
          <PosKey
            size="sm"
            tone="nav"
            onClick={async () => {
              try {
                await api("/admin/pos-mutate", { method: "POST", json: { sku, unit_price: price ? Number(price) : null, on_hand: stock ? Number(stock) : null } });
                setMsg(t("mutated"));
                onDone();
              } catch (e) {
                setMsg(e instanceof ApiError ? e.message : String(e));
              }
            }}
          >
            {t("apply")}
          </PosKey>
          <PosKey
            size="sm"
            onClick={async () => {
              await api("/admin/pos-reset", { method: "POST" });
              setMsg(t("reset_done"));
              onDone();
            }}
          >
            {t("reset")}
          </PosKey>
        </div>
        {msg && <p className="screen-note">{msg}</p>}
        <p className="screen-note">{t("demo_only")}</p>
      </div>
    </details>
  );
}
