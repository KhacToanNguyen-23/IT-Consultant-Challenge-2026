"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import clsx from "clsx";
import { AlertTriangle, ArrowRight, Ban, CheckCircle2, Download, Loader2, Printer, RefreshCw, Send, Wrench } from "lucide-react";
import { api, ApiError, API_URL, fileUrl, fmtMoney, fmtTime, type QuoteView } from "@/client/api";
import { useI18n, type Key } from "@/client/i18n";
import { StatePill } from "@/components/StatusBadge";

const FLOW = ["SAVED", "SENT", "CUST", "PREPARING", "CONFIRMED"] as const;

export default function QuoteDetailPage({ params }: { params: { id: string } }) {
  const { t, lang } = useI18n();
  const [q, setQ] = useState<QuoteView | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [channel, setChannel] = useState("email");
  const [notice, setNotice] = useState<string | null>(null);

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

  if (!q) return <div className="py-20 text-center text-slate-500">{error || <Loader2 className="mx-auto animate-spin" />}</div>;

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

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-end gap-3">
        <div>
          <div className="text-xs text-slate-500">
            <Link href="/quotes" className="hover:underline">
              {t("back_quotes")}
            </Link>{" "}
            · {t("flow2_short")}
          </div>
          <h1 className="text-xl font-bold">
            <span className="font-mono">{q.quote_id}</span> <StatePill status={q.status} />
          </h1>
        </div>
        <ol className="flex flex-wrap items-center gap-1 text-xs">
          {FLOW.map((k, i) => (
            <li key={k} className="flex items-center gap-1">
              <span className={clsx("rounded-full px-2 py-0.5 font-semibold", reached(k) ? "bg-emerald-100 text-emerald-900" : "bg-slate-200 text-slate-600")}>{t(`qf_${k}` as Key)}</span>
              {i < FLOW.length - 1 && <ArrowRight size={12} className="text-slate-300" />}
            </li>
          ))}
        </ol>
      </div>

      {(q.status === "EXPIRED" || q.status === "CANCELLED") && (
        <div className="flex items-center gap-2 rounded-md border border-red-400 bg-red-50 px-3 py-2 text-sm font-semibold text-red-900">
          <Ban size={16} /> {q.status === "EXPIRED" ? t("expired_banner", { date: q.valid_until }) : t("cancelled_banner")} {t("cannot_confirm_short")}
        </div>
      )}
      {error && (
        <p role="alert" className="rounded-md border border-red-300 bg-red-50 px-3 py-2 text-sm text-red-900">
          {error}
        </p>
      )}
      {notice && (
        <p role="status" className="rounded-md border border-emerald-300 bg-emerald-50 px-3 py-2 text-sm text-emerald-900">
          {notice}
        </p>
      )}
      {q.live_error && (
        <p className="flex items-center gap-2 rounded-md border border-amber-500 bg-amber-50 px-3 py-2 text-sm text-amber-950">
          <AlertTriangle size={16} /> {q.live_error}
        </p>
      )}

      <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_340px]">
        <div className="space-y-3">
          <div className="grid gap-3 rounded-lg border border-slate-200 bg-white p-4 text-sm shadow-sm sm:grid-cols-3">
            <Info k="Client ID" v={`${q.client_id}${q.customer_type ? ` · ${q.customer_type}` : ""}`} />
            <Info k={t("valid_until")} v={q.valid_until} />
            <Info k={t("discount")} v={`${q.applied_discount_tier} (${(q.discount_rate * 100).toFixed(0)}%)`} />
            <Info k={t("price_source")} v={q.price_source} />
            <Info k={t("price_time")} v={fmtTime(q.price_captured_at)} />
            <Info k={t("snapshot_total")} v={fmtMoney(q.snapshot_total, q.currency)} />
            <p className="rounded border border-amber-400 bg-amber-50 px-2 py-1 text-xs font-semibold text-amber-950 sm:col-span-3">{q.disclaimer}</p>
          </div>

          <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white shadow-sm">
            <div className="flex flex-wrap items-center gap-3 border-b border-slate-200 px-4 py-2 text-sm">
              <span className="font-semibold">{t("snap_vs_live")}</span>
              {q.live_checked_at && <span className="text-xs text-slate-500">{t("checked_at", { time: fmtTime(q.live_checked_at) })}</span>}
              {changedCount > 0 && <span className="rounded bg-amber-100 px-2 py-0.5 text-xs font-semibold text-amber-900">{t("n_changed", { n: changedCount })}</span>}
              {shortCount > 0 && <span className="rounded bg-red-100 px-2 py-0.5 text-xs font-semibold text-red-900">{t("n_short", { n: shortCount })}</span>}
              <button onClick={() => act("reload", async () => {}, t("rechecked"))} className="ml-auto inline-flex items-center gap-1 text-xs font-semibold text-blue-800 hover:underline">
                <RefreshCw size={12} /> {t("recheck")}
              </button>
            </div>
            <table className="w-full min-w-[820px] text-sm">
              <thead className="bg-slate-50 text-left text-xs uppercase tracking-wide text-slate-500">
                <tr>
                  <th className="px-3 py-2">#</th>
                  <th className="px-3 py-2">{t("col_sku_product")}</th>
                  <th className="px-3 py-2">{t("col_qty_short")}</th>
                  <th className="px-3 py-2">{t("col_net_price")}</th>
                  <th className="px-3 py-2">{t("col_stock")}</th>
                  <th className="px-3 py-2">{t("col_current_line")}</th>
                </tr>
              </thead>
              <tbody>
                {q.lines.map((l) => {
                  const priceChanged = l.changed_fields.includes("price");
                  const stockChanged = l.changed_fields.includes("stock");
                  return (
                    <tr key={l.line_no} className={clsx("border-t border-slate-100 align-top", (priceChanged || stockChanged) && "bg-amber-50/60", l.alternative_required && "bg-red-50/60")}>
                      <td className="px-3 py-2 tabular text-slate-500">{l.line_no}</td>
                      <td className="px-3 py-2">
                        <div className="font-mono text-xs text-slate-500">{l.sku}</div>
                        <div className="font-medium">{l.name}</div>
                        <div className="text-xs text-slate-500">{l.raw_customer_input}</div>
                      </td>
                      <td className="px-3 py-2 tabular">
                        {l.quantity} × {l.selling_unit}
                      </td>
                      <td className="px-3 py-2 tabular">
                        <Diff before={fmtMoney(l.snapshot.unit_price, q.currency)} after={l.live ? fmtMoney(l.live.unit_price, q.currency) : null} changed={priceChanged} />
                      </td>
                      <td className="px-3 py-2 tabular">
                        <Diff before={String(l.snapshot.on_hand)} after={l.live?.on_hand != null ? String(l.live.on_hand) : null} changed={stockChanged} />
                        {l.alternative_required && <div className="mt-1 text-xs font-semibold text-red-900">{t("short_alt")}</div>}
                      </td>
                      <td className="px-3 py-2 text-xs">
                        {l.current_line && (
                          <>
                            <div>{t(`ls_${l.current_line.line_status}` as Key)}</div>
                            {l.current_line.final_sku !== l.sku && <div className="text-emerald-800">→ {l.current_line.final_sku}</div>}
                            {l.current_line.fulfillment_action && <div className="text-slate-500">{l.current_line.fulfillment_action}</div>}
                          </>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
            <p className="border-t border-slate-200 px-4 py-2 text-xs text-slate-500">{t("quote_foot")}</p>
          </div>
        </div>

        <aside className="space-y-3">
          <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
            <h2 className="font-semibold">{t("actions")}</h2>
            <div className="mt-3 space-y-2">
              <a href={printUrl("quote")} target="_blank" rel="noreferrer" className={btn("outline")}>
                <Printer size={15} /> {t("print_quote")}
              </a>
              {can("SEND") && (
                <button className={btn("outline")} disabled={!!busy} onClick={() => act("send", () => api(`/quotes/${q.quote_id}/transitions`, { method: "POST", json: { to_status: "SENT" } }).then(() => undefined), t("marked_sent"))}>
                  <Send size={15} /> {t("mark_sent")}
                </button>
              )}
              {can("RECORD_CUSTOMER_CONFIRMATION") && (
                <div className="rounded-md border border-slate-200 p-2">
                  <div className="text-xs font-semibold text-slate-700">{t("cust_conf_via")}</div>
                  <div className="mt-1 flex gap-2">
                    <select value={channel} onChange={(e) => setChannel(e.target.value)} className="flex-1 rounded border border-slate-300 px-2 py-1 text-sm">
                      <option value="email">{t("ch_email")}</option>
                      <option value="phone">{t("ch_phone")}</option>
                      <option value="in_store">{t("ch_in_store")}</option>
                    </select>
                    <button
                      disabled={!!busy}
                      onClick={() => act("cust", () => api(`/quotes/${q.quote_id}/customer-confirmation`, { method: "POST", json: { channel } }), t("recorded"))}
                      className="rounded bg-slate-900 px-3 py-1 text-xs font-semibold text-white disabled:opacity-50"
                    >
                      {t("record")}
                    </button>
                  </div>
                </div>
              )}
              {q.customer_confirmed_at && <p className="text-xs text-emerald-800">{t("cust_confirmed_at", { time: fmtTime(q.customer_confirmed_at), by: q.customer_confirmed_by || "" })}</p>}
              {can("PREPARE") && (
                <button className={btn("primary")} disabled={!!busy} onClick={() => act("prepare", () => api<QuoteView>(`/quotes/${q.quote_id}/prepare`, { method: "POST" }), t("prepared"))}>
                  {busy === "prepare" ? <Loader2 size={15} className="animate-spin" /> : <RefreshCw size={15} />} {t("prepare")}
                </button>
              )}
              {!q.customer_confirmed_at && ["SAVED", "SENT"].includes(q.status) && <p className="text-xs text-slate-500">{t("prepare_locked")}</p>}
              {can("PRINT_PICK_SLIP") && (
                <a href={printUrl("pick-slip")} target="_blank" rel="noreferrer" className={btn("outline")}>
                  <Printer size={15} /> {t("print_pick")}
                </a>
              )}
              {can("CONFIRM") &&
                (blockers > 0 ? (
                  <Link href={`/sessions/${q.session_id}`} className={btn("primary")}>
                    {t("resolve_short", { n: blockers })}
                  </Link>
                ) : (
                  <button className={btn("success")} disabled={!!busy} onClick={() => act("confirm", () => api(`/quotes/${q.quote_id}/confirm`, { method: "POST" }).then(() => undefined), t("confirmed_via_connector"))}>
                    {busy === "confirm" ? <Loader2 size={15} className="animate-spin" /> : <CheckCircle2 size={15} />} {t("confirm_send")}
                  </button>
                ))}
              {q.status === "CONFIRMED" && (
                <div className={clsx("rounded-md border p-2 text-sm", q.order.pos_order_ref ? "border-emerald-400 bg-emerald-50" : "border-amber-500 bg-amber-50")}>
                  {q.order.pos_order_ref ? (
                    <>
                      {t("pos_received")} <b className="font-mono">{q.order.pos_order_ref}</b>
                    </>
                  ) : (
                    <>
                      {t("pos_failed_csv")} <b className="font-mono">{q.order.fulfillment_reference}</b>
                      {q.order.csv_download_url && (
                        <a href={fileUrl(q.order.csv_download_url)} className="mt-1 flex items-center gap-1 font-semibold text-amber-900 underline">
                          <Download size={14} /> {t("download_csv_short")}
                        </a>
                      )}
                    </>
                  )}
                </div>
              )}
              <Link href={`/sessions/${q.session_id}`} className="block text-center text-xs font-semibold text-blue-800 hover:underline">
                {t("view_review", { id: q.order_session_id })}
              </Link>
              {can("CANCEL") && (
                <button className={btn("danger")} disabled={!!busy} onClick={() => act("cancel", () => api(`/quotes/${q.quote_id}/transitions`, { method: "POST", json: { to_status: "CANCELLED" } }).then(() => undefined), t("cancelled_msg"))}>
                  <Ban size={15} /> {t("cancel_quote")}
                </button>
              )}
            </div>
          </div>
          {["SAVED", "SENT", "PREPARING"].includes(q.status) && <DemoTools q={q} onDone={load} />}
        </aside>
      </div>
    </div>
  );
}

function btn(kind: "primary" | "outline" | "success" | "danger") {
  return clsx(
    "flex w-full items-center justify-center gap-2 rounded-md px-3 py-2 text-sm font-semibold focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-600 disabled:opacity-50",
    kind === "primary" && "bg-violet-700 text-white hover:bg-violet-800",
    kind === "success" && "bg-emerald-700 text-white hover:bg-emerald-800",
    kind === "outline" && "border border-slate-300 bg-white text-slate-800 hover:bg-slate-50",
    kind === "danger" && "border border-red-300 bg-white text-red-800 hover:bg-red-50"
  );
}

function Info({ k, v }: { k: string; v: string }) {
  return (
    <div>
      <div className="text-xs text-slate-500">{k}</div>
      <div className="font-medium">{v}</div>
    </div>
  );
}

function Diff({ before, after, changed }: { before: string; after: string | null; changed: boolean }) {
  if (!after || !changed) return <span>{before}</span>;
  return (
    <span>
      <span className="text-slate-400 line-through">{before}</span> <span className="font-semibold text-amber-900">→ {after}</span>
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
    <details className="rounded-lg border border-dashed border-slate-300 bg-white p-3 text-sm">
      <summary className="flex cursor-pointer items-center gap-2 font-semibold text-slate-600">
        <Wrench size={14} /> {t("demo_tools")}
      </summary>
      <div className="mt-2 space-y-2">
        <select value={sku} onChange={(e) => setSku(e.target.value)} className="w-full rounded border border-slate-300 px-2 py-1">
          {skus.map((s) => (
            <option key={s}>{s}</option>
          ))}
        </select>
        <div className="grid grid-cols-2 gap-2">
          <input value={price} onChange={(e) => setPrice(e.target.value)} placeholder={t("new_list_price")} inputMode="decimal" className="rounded border border-slate-300 px-2 py-1" />
          <input value={stock} onChange={(e) => setStock(e.target.value)} placeholder={t("new_stock")} inputMode="decimal" className="rounded border border-slate-300 px-2 py-1" />
        </div>
        <div className="flex gap-2">
          <button
            className="flex-1 rounded bg-slate-700 px-2 py-1 text-xs font-semibold text-white"
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
          </button>
          <button
            className="rounded border border-slate-300 px-2 py-1 text-xs"
            onClick={async () => {
              await api("/admin/pos-reset", { method: "POST" });
              setMsg(t("reset_done"));
              onDone();
            }}
          >
            {t("reset")}
          </button>
        </div>
        {msg && <p className="text-xs text-slate-500">{msg}</p>}
        <p className="text-[11px] text-slate-400">{t("demo_only")}</p>
      </div>
    </details>
  );
}
