"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import clsx from "clsx";
import { AlertTriangle } from "lucide-react";
import { fmtMoney, fmtTime, type Line, type SessionView } from "@/client/api";
import { useI18n, type Key } from "@/client/i18n";
import { AttributeChips, BandBadge, LineStatusBadge, RoundedBadge, StockBadge } from "@/components/StatusBadge";
import ListPagination from "@/components/pos/ListPagination";

const PAGE_SIZE = 10;
type T = ReturnType<typeof useI18n>["t"];
export const attrLabel = (t: T, a: string) => t(`a_${a}` as Key);
export const unitLabel = (t: T, u: string) => t(`u_${u}` as Key);

/** List-price amount for a line; null until both the SKU and the selling quantity are known. */
export function lineAmount(l: Line): number | null {
  return l.unit_price != null && l.conversion.selling_quantity != null ? l.unit_price * l.conversion.selling_quantity : null;
}

function priority(l: Line): number {
  if (l.line_status === "NEEDS_CLARIFICATION") return 0;
  if (l.line_status === "SUBSTITUTE_PROPOSED") return 1;
  if (l.stock.status === "OUT_OF_STOCK" || l.stock.status === "PARTIAL") return 2;
  if (l.match.band !== "HIGH") return 3;
  return 4;
}

/** The one thing the associate must see on an exception line, in plain words (never a guess). */
function attention(l: Line, t: T): { tone: "stop" | "warn"; text: string } | null {
  const r = l.match.reasons as { missing?: string[]; ambiguous?: boolean } | undefined;
  const need = l.conversion.selling_quantity ?? "?";
  const have = l.stock.on_hand ?? 0;
  if (l.line_status === "SUBSTITUTE_PROPOSED")
    return { tone: "stop", text: l.stock.status === "PARTIAL" ? t("attn_partial", { have, need }) : t("attn_out") };
  if (l.line_status === "NEEDS_CLARIFICATION") {
    if (!l.match.sku && l.match.candidates.length === 0) return { tone: "stop", text: t("attn_nocand") };
    if (r?.missing?.length) return { tone: "stop", text: t("attn_missing", { list: r.missing.map((m) => attrLabel(t, m)).join(", ") }) };
    if (l.conversion.selling_quantity == null && l.conversion.blocked_reason) return { tone: "stop", text: l.conversion.blocked_reason };
    return r?.ambiguous ? { tone: "warn", text: t("attn_ambiguous") } : { tone: "warn", text: t("attn_decide") };
  }
  if (l.line_status !== "CUSTOMER_ACCEPTED" && l.stock.status === "OUT_OF_STOCK") return { tone: "stop", text: t("attn_out_only") };
  if (l.line_status !== "CUSTOMER_ACCEPTED" && l.stock.status === "PARTIAL") return { tone: "warn", text: t("attn_partial_only", { have, need }) };
  return null;
}

function rowTone(l: Line) {
  if (l.line_status === "NEEDS_CLARIFICATION") return "warn";
  if (l.line_status === "CUSTOMER_ACCEPTED") return "good";
  if (l.line_status === "SUBSTITUTE_PROPOSED" || l.stock.status === "OUT_OF_STOCK" || l.stock.status === "PARTIAL") return "bad";
  return l.match.band === "REVIEW" ? "soft" : "good";
}

interface Props {
  session: SessionView;
  selected: number | null;
  onSelect: (lineNo: number | null) => void;
}

export default function TicketLines({ session, selected, onSelect }: Props) {
  const { t } = useI18n();
  const sorted = useMemo(() => [...session.lines].sort((a, b) => priority(a) - priority(b) || a.line_no - b.line_no), [session.lines]);
  const [page, setPage] = useState(0);
  const pendingFocus = useRef<number | null>(null);
  const rows = useRef<Record<number, HTMLDivElement | null>>({});

  useEffect(() => {
    if (selected != null) rows.current[selected]?.scrollIntoView({ block: "nearest" });
  }, [selected]);
  useEffect(() => {
    if (selected == null) return;
    const index = sorted.findIndex((line) => line.line_no === selected);
    if (index >= 0) setPage(Math.floor(index / PAGE_SIZE));
  }, [selected, sorted]);
  useEffect(() => {
    if (pendingFocus.current != null) {
      rows.current[pendingFocus.current]?.focus();
      pendingFocus.current = null;
    }
  }, [page]);
  useEffect(() => setPage((current) => Math.min(current, Math.max(0, Math.ceil(sorted.length / PAGE_SIZE) - 1))), [sorted.length]);

  const onRowKey = (e: React.KeyboardEvent, idx: number, l: Line) => {
    if (e.key === "ArrowDown" || e.key === "ArrowUp") {
      e.preventDefault();
      const nextIndex = idx + (e.key === "ArrowDown" ? 1 : -1);
      const next = sorted[nextIndex];
      if (next) {
        const nextPage = Math.floor(nextIndex / PAGE_SIZE);
        if (nextPage !== page) {
          pendingFocus.current = next.line_no;
          setPage(nextPage);
        } else rows.current[next.line_no]?.focus();
      }
    } else if (e.key === "Enter") {
      e.preventDefault();
      onSelect(selected === l.line_no ? null : l.line_no);
    }
  };

  const exceptions = sorted.filter((l) => priority(l) <= 3).length;

  const row = (l: Line, idx: number) => {
    const amount = lineAmount(l);
    const attn = session.analyzed ? attention(l, t) : null;
    const isSelected = selected === l.line_no;
    return (
      <div
        key={l.line_id}
        ref={(el) => {
          rows.current[l.line_no] = el;
        }}
        role="button"
        tabIndex={0}
        aria-pressed={selected === l.line_no}
        onClick={() => onSelect(selected === l.line_no ? null : l.line_no)}
        onKeyDown={(e) => onRowKey(e, idx, l)}
        className={clsx("tline", session.analyzed && `tline--${rowTone(l)}`, selected === l.line_no && "is-selected")}
      >
        <div className="tline-no tabular">{l.line_no}</div>
        <div className="min-w-0">
          {l.line_status === "CUSTOMER_ACCEPTED" && <div className="font-mono text-xs soft line-through">{l.match.sku}</div>}
          {session.analyzed && l.line_status === "NEEDS_CLARIFICATION" && l.final_sku && <div className="line-match-label">{t("suggested_unconfirmed")}</div>}
          <div className={clsx("text-[17px] font-bold leading-snug", session.analyzed && l.line_status === "NEEDS_CLARIFICATION" ? "text-slate-500" : "text-[#12304d]")}>{l.final_name || l.parsed.name || <i className="text-red-800">{t("unreadable")}</i>}</div>
          <div className="mt-0.5 flex flex-wrap items-baseline gap-x-2 text-[12.5px] text-slate-500">
            {l.final_sku ? <span className="font-mono">{l.final_sku}</span> : session.analyzed && <span className="font-semibold text-amber-800">{t("no_sku")}</span>}
            <span className="min-w-0 truncate" title={l.source.text}>“{l.source.text}”</span>
          </div>
          {attn && (
            <div className={clsx("line-attn", `line-attn--${attn.tone}`)}>
              <AlertTriangle size={15} aria-hidden /> {attn.text}
            </div>
          )}
          {isSelected && l.parsed.warnings.includes("n_x_l_review") && <div className="text-xs text-amber-800">N × L: {l.conversion.requested}</div>}
          {isSelected && <AttributeChips chips={l.chips} />}
        </div>
        <div className="tline-qty tabular">
          <div>
            {l.parsed.quantity ?? "?"} {l.parsed.unit ? unitLabel(t, l.parsed.unit) : <span className="text-amber-800">{l.parsed.unit_raw || t("unit_q")}</span>}
          </div>
          {l.conversion.selling_quantity != null ? (
            <div className="font-semibold">
              → {l.conversion.selling_quantity} × {l.conversion.selling_unit}
            </div>
          ) : (
            session.analyzed && <div className="text-xs text-amber-800">{l.conversion.blocked_reason}</div>
          )}
          {isSelected && l.conversion.formula && <div className="text-xs soft">{l.conversion.formula}</div>}
          {l.conversion.rounded && <RoundedBadge />}
        </div>
        <div className="tline-check flex flex-wrap content-start items-center gap-1">
          {session.analyzed && (l.line_status === "CUSTOMER_ACCEPTED" || attn) && <LineStatusBadge status={l.line_status} />}
          {session.analyzed && !attn && l.line_status !== "CUSTOMER_ACCEPTED" && (
            <>
              <StockBadge stock={l.stock} />
              {l.match.match_score != null && <span className="text-[11px] text-slate-400">{t("match_score", { score: l.match.match_score.toFixed(2) })}</span>}
            </>
          )}
        </div>
        <div className="tline-amount">{amount != null ? fmtMoney(amount, "").trim() : "—"}</div>
      </div>
    );
  };

  const flagged = sorted.filter((l) => priority(l) <= 3);
  const clean = sorted.filter((l) => priority(l) > 3);
  const pageRows = sorted.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE);

  return (
    <>
      <div className="tline-head" aria-hidden>
        <span>#</span>
        <span>{t("col_product")}</span>
        <span>{t("col_qty_sell")}</span>
        <span>{t("col_check")}</span>
        <span className="text-right">{t("col_amount")}</span>
      </div>
      {session.analyzed && exceptions > 0 ? (
        <>
          {pageRows.some((l) => priority(l) <= 3) && <div className="tline-group text-amber-900">{t("group_attention", { n: flagged.length })}</div>}
          {pageRows.filter((l) => priority(l) <= 3).map((l) => row(l, sorted.indexOf(l)))}
          {pageRows.some((l) => priority(l) > 3) && <div className="tline-group text-emerald-800">{t("group_ok", { n: clean.length })}</div>}
          {pageRows.filter((l) => priority(l) > 3).map((l) => row(l, sorted.indexOf(l)))}
        </>
      ) : (
        pageRows.map((l) => row(l, sorted.indexOf(l)))
      )}
      <ListPagination total={sorted.length} page={page} pageSize={PAGE_SIZE} onPageChange={setPage} />
    </>
  );
}
