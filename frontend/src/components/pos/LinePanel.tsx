"use client";

import { useState } from "react";
import { Check, Loader2, Search, X } from "lucide-react";
import { api, ApiError, fmtMoney, fmtTime, UNITS, type Line, type SessionView } from "@/client/api";
import { useI18n } from "@/client/i18n";
import { BandBadge } from "@/components/StatusBadge";
import { Notice, PosKey } from "./Terminal";
import { attrLabel, unitLabel } from "./TicketLines";

type Run = (fn: () => Promise<SessionView>) => Promise<void>;

interface Props {
  session: SessionView;
  line: Line;
  onChange: (v: SessionView) => void;
  onClose: () => void;
}

/** Inspector for one ticket line. Manual catalog search stays visible when AI is degraded. */
export default function LinePanel({ session, line, onChange, onClose }: Props) {
  const { t } = useI18n();
  const locked = session.locked;
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const run: Run = async (fn) => {
    setBusy(true);
    setErr(null);
    try {
      onChange(await fn());
    } catch (e) {
      setErr(e instanceof ApiError ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  };
  const select = (sku: string, decision: string, reason?: string) =>
    run(() => api(`/sessions/${session.session_id}/lines/${line.line_no}/selection`, { method: "PUT", json: { sku, decision, reason: reason ?? null } }));

  const searchOpen = session.ai_degraded || (line.line_status === "NEEDS_CLARIFICATION" && line.match.candidates.length === 0);

  return (
    <div className="space-y-3">
      <div className="flex items-start gap-2">
        <div className="min-w-0 flex-1">
          <h2 className="screen-title">{t("line_n", { n: line.line_no })}</h2>
          <div className="font-mono text-xs soft">
            {t("source")}: {line.source.text}
          </div>
          {session.analyzed && (
            <div className={`mt-2 inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-semibold ${session.ai_degraded ? "bg-amber-100 text-amber-950" : "bg-blue-50 text-blue-900"}`}>
              <span className={`lamp ${session.ai_degraded ? "lamp--warn" : "lamp--ok"}`} aria-hidden />
              {session.ai_degraded ? t("rules_fallback_mode") : t("ai_match_mode")}
            </div>
          )}
        </div>
        <PosKey size="sm" hotkey="Escape" onClick={onClose} className="w-20 flex-none">
          {t("key_close")}
        </PosKey>
      </div>

      {err && (
        <Notice tone="bad" alert>
          {err}
        </Notice>
      )}

      {!session.analyzed ? (
        <ParseEditor session={session} line={line} locked={locked} run={run} />
      ) : (
        <>
          <Resolve session={session} line={line} busy={busy} select={select} />
          {!locked && !session.quote && (
            <>
              <details className="inspector-details" open={searchOpen}>
                <summary className="tile font-semibold">{t("manual_search_title")}</summary>
                <div className="pt-3">
                  <CatalogSearch initial={line.parsed.name || line.source.text || ""} busy={busy} onPick={(sku) => select(sku, sku === line.match.sku ? "SKU_KEPT" : "SKU_EDITED")} />
                </div>
              </details>
              <details className="inspector-details">
                <summary className="tile font-semibold">{t("tab_edit")}</summary>
                <div className="pt-3">
                  <ParseEditor session={session} line={line} locked={locked} run={run} />
                </div>
              </details>
            </>
          )}
        </>
      )}
    </div>
  );
}

function Resolve({ session, line, busy, select }: { session: SessionView; line: Line; busy: boolean; select: (sku: string, decision: string, reason?: string) => Promise<void> }) {
  const { t } = useI18n();
  const locked = session.locked;
  const reasons = line.match.reasons as Line["match"]["reasons"] & { missing?: string[]; ambiguous?: boolean };
  const list = (xs: string[]) => xs.map((m) => attrLabel(t, m)).join(", ");
  const substitute = line.line_status === "SUBSTITUTE_PROPOSED" && !locked;
  const accepted = line.line_status === "CUSTOMER_ACCEPTED" && !locked;
  const clarify = line.line_status === "NEEDS_CLARIFICATION" && !locked;

  return (
    <div className="space-y-3">
      {substitute && <Alternatives line={line} rate={session.discount_rate} busy={busy} onAccept={(sku) => select(sku, "SUBSTITUTION_ACCEPTED")} onReject={(reason) => select(line.match.sku!, "SUBSTITUTION_REJECTED", reason)} />}

      {accepted && (
        <Notice tone="good">
          {t("accepted_note", { from: line.match.sku || "", to: line.final_sku || "", time: fmtTime(line.substitution.accepted_at) })}{" "}
          <button type="button" className="font-semibold text-red-800 underline" disabled={busy} onClick={() => select(line.match.sku!, "SUBSTITUTION_REJECTED", t("customer_changed_mind"))}>
            {t("undo")}
          </button>
        </Notice>
      )}

      {clarify && line.match.candidates.length > 0 && (
        <div>
          <div className="mb-1.5 font-semibold">{t("candidates_title")}</div>
          <ul className="space-y-1.5">
            {line.match.candidates.map((c) => (
              <li key={c.sku}>
                <button type="button" disabled={busy} className="tile" onClick={() => select(c.sku, c.sku === line.match.sku ? "SKU_KEPT" : "SKU_EDITED")}>
                  <span className="block font-semibold leading-snug">{c.name}</span>
                  <span className="mt-1 flex flex-wrap items-center gap-2">
                    <BandBadge band={c.band} score={c.score} />
                    <span className="font-mono text-xs soft">{c.sku}</span>
                  </span>
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}

      {clarify && line.match.candidates.length === 0 && <Notice tone="warn">{t("line_no_candidates")}</Notice>}
      {!substitute && !accepted && !clarify && <p className="font-semibold">{t("line_ok_hint")}</p>}

      {line.match.sku && (reasons?.matched?.length || reasons?.mismatched?.length || reasons?.missing?.length || reasons?.ambiguous || line.llm_attributes?.length) && (
        <details className="inspector-details">
          <summary className="cursor-pointer text-xs font-semibold text-slate-600">{t("why_title")}</summary>
          <div className="mt-2 space-y-1 text-xs leading-relaxed">
            {reasons?.matched?.length ? <div>{t("why_matched", { list: list(reasons.matched) })}</div> : null}
            {reasons?.mismatched?.length ? <div className="text-red-800">{t("why_mismatched", { list: list(reasons.mismatched) })}</div> : null}
            {reasons?.missing?.length ? <div className="text-amber-900">{t("why_missing", { list: list(reasons.missing) })}</div> : null}
            {reasons?.ambiguous && <div className="text-amber-900">{t("why_ambiguous")}</div>}
            {line.llm_attributes?.length ? <div className="text-violet-800">{t("why_llm", { list: list(line.llm_attributes) })}</div> : null}
          </div>
        </details>
      )}
    </div>
  );
}

function ParseEditor({ session, line, locked, run }: { session: SessionView; line: Line; locked: boolean; run: Run }) {
  const { t } = useI18n();
  const [name, setName] = useState(line.parsed.name || "");
  const [qty, setQty] = useState(line.parsed.quantity?.toString().replace(".", ",") || "");
  const [unit, setUnit] = useState(line.parsed.unit || "");
  const parsedQty = Number(qty.replace(",", "."));
  const qtyChanged = !!qty && parsedQty !== line.parsed.quantity;
  const dirty = name !== (line.parsed.name || "") || qtyChanged || unit !== (line.parsed.unit || "");

  const save = () =>
    run(() =>
      api(`/sessions/${session.session_id}/lines/${line.line_no}`, {
        method: "PATCH",
        json: {
          item_text: name !== (line.parsed.name || "") ? name : null,
          requested_qty: qtyChanged ? parsedQty : null,
          requested_unit: unit && unit !== line.parsed.unit ? unit : null,
        },
      })
    );

  return (
    <form
      className="space-y-2.5"
      onSubmit={(e) => {
        e.preventDefault();
        if (dirty) save();
      }}
    >
      <label className="block font-semibold">
        {t("item_name")}
        <input disabled={locked} value={name} onChange={(e) => setName(e.target.value)} className="field mt-1 font-normal" />
      </label>

      <div className="grid grid-cols-[minmax(0,1.15fr)_minmax(0,1fr)] gap-3">
        <div>
          <label className="block font-semibold">
            {t("quantity")}
            <input disabled={locked} inputMode="decimal" value={qty} onChange={(e) => setQty(e.target.value)} className="field font-mono mt-1 text-right text-lg font-semibold tabular" />
          </label>
        </div>
        <label className="block font-semibold">
          {t("unit")}
          <select disabled={locked} value={unit} onChange={(e) => setUnit(e.target.value)} className="field mt-1 font-normal">
            <option value="">{t("unit_q")}</option>
            {UNITS.map((u) => <option key={u} value={u}>{unitLabel(t, u)}</option>)}
          </select>
        </label>
      </div>

      {line.parsed.warnings.includes("ambiguous_unit_m") ? (
        <Notice tone="warn">{t("ambiguous_unit_m_hint")}</Notice>
      ) : (
        line.parsed.unit_raw && !line.parsed.unit && <Notice tone="warn">{t("unknown_unit_hint", { u: line.parsed.unit_raw })}</Notice>
      )}

      {!locked && (
        <button type="submit" disabled={!dirty} className="key key--nav w-full !items-center disabled:!bg-slate-400">
          <span className="key-label">{session.analyzed ? t("save_reanalyze") : t("save")}</span>
        </button>
      )}
    </form>
  );
}

function Alternatives({ line, rate, busy, onAccept, onReject }: { line: Line; rate: number; busy: boolean; onAccept: (sku: string) => void; onReject: (reason: string) => void }) {
  const { t } = useI18n();
  const [reason, setReason] = useState("");
  return (
    <div className="space-y-2">
      <Notice tone="bad">
        <b>{line.stock.status === "PARTIAL" ? t("partial_need", { have: line.stock.on_hand ?? 0, need: line.conversion.selling_quantity ?? "?" }) : t("out_here")}</b> {t("safe_subs")}
      </Notice>
      <ul className="space-y-2">
        {line.alternatives.map((a) => (
          <li key={a.sku} className="rounded border border-[#a6aca7] bg-white p-2.5">
            <div className="font-semibold leading-snug">{a.name}</div>
            <div className="font-mono text-xs soft">{a.sku}</div>
            {a.different_grade && <span className="mt-1 inline-block rounded bg-blue-50 px-1.5 text-[11px] text-blue-900">{t("higher_grade")}</span>}
            <div className="mt-1 text-xs tabular">
              {t("in_stock_n", { n: a.on_hand })}, {a.needed_quantity} × {a.selling_unit}, Δ {a.total_price_delta >= 0 ? "+" : ""}
              {fmtMoney(a.total_price_delta * (1 - rate), a.currency)} {t(rate > 0 ? "delta_net" : "delta_list")}
            </div>
            <div className="mt-0.5 text-xs soft">{a.reasons.join(", ")}</div>
            <PosKey size="sm" tone="go" icon={<Check size={16} />} disabled={busy} onClick={() => onAccept(a.sku)} className="mt-2 w-full">
              {t("customer_accepts")}
            </PosKey>
          </li>
        ))}
      </ul>
      <label className="block font-semibold">
        {t("reject_reason_ph")}
        <input value={reason} onChange={(e) => setReason(e.target.value)} className="field mt-1 font-normal" />
      </label>
      <PosKey size="sm" tone="void" icon={<X size={16} />} disabled={busy || !reason.trim()} onClick={() => onReject(reason)} className="w-full">
        {t("customer_rejects")}
      </PosKey>
    </div>
  );
}

function CatalogSearch({ initial, busy, onPick }: { initial: string; busy: boolean; onPick: (sku: string) => void }) {
  const { t } = useI18n();
  const [q, setQ] = useState(initial);
  const [items, setItems] = useState<{ sku: string; name: string; unit_price: number; currency: string; selling_unit: string }[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const search = async () => {
    setLoading(true);
    setErr(null);
    try {
      setItems((await api(`/catalog/search?q=${encodeURIComponent(q)}&limit=8`)).items);
    } catch (e) {
      setErr(e instanceof ApiError ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-2">
      <form
        className="flex gap-2"
        onSubmit={(e) => {
          e.preventDefault();
          search();
        }}
      >
        <input value={q} onChange={(e) => setQ(e.target.value)} placeholder={t("search_ph")} aria-label={t("manual_search_title")} className="field min-w-0 flex-1" />
        <button type="submit" className="key key--nav key--sm flex-none !flex-row !items-center gap-1.5">
          {loading ? <Loader2 size={16} className="animate-spin" aria-hidden /> : <Search size={16} aria-hidden />} {t("search")}
        </button>
      </form>
      {err && (
        <Notice tone="bad" alert>
          {err}
        </Notice>
      )}
      {items?.length === 0 && <p className="screen-note">{t("no_results")}</p>}
      {items && items.length > 0 && (
        <ul className="space-y-1.5">
          {items.map((i) => (
            <li key={i.sku}>
              <button type="button" disabled={busy} className="tile" onClick={() => onPick(i.sku)}>
                <span className="block font-semibold leading-snug">{i.name}</span>
                <span className="mt-0.5 flex justify-between gap-2 text-xs">
                  <span className="font-mono soft">{i.sku}</span>
                  <span className="tabular">{fmtMoney(i.unit_price, i.currency)}</span>
                </span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
