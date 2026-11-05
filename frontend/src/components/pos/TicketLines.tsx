"use client";

import { useEffect, useMemo, useRef } from "react";
import clsx from "clsx";
import { fmtMoney, fmtTime, type Line, type SessionView } from "@/client/api";
import { useI18n, type Key } from "@/client/i18n";
import { AttributeChips, BandBadge, LineStatusBadge, RoundedBadge, StockBadge } from "@/components/StatusBadge";

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
  const rows = useRef<Record<number, HTMLDivElement | null>>({});

  useEffect(() => {
    if (selected != null) rows.current[selected]?.scrollIntoView({ block: "nearest" });
  }, [selected]);

  const onRowKey = (e: React.KeyboardEvent, idx: number, l: Line) => {
    if (e.key === "ArrowDown" || e.key === "ArrowUp") {
      e.preventDefault();
      const next = sorted[idx + (e.key === "ArrowDown" ? 1 : -1)];
      if (next) rows.current[next.line_no]?.focus();
    } else if (e.key === "Enter") {
      e.preventDefault();
      onSelect(selected === l.line_no ? null : l.line_no);
    }
  };

  const exceptions = sorted.filter((l) => priority(l) <= 3).length;

  const row = (l: Line, idx: number) => {
    const amount = lineAmount(l);
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
          <div className="line-source-label">{t("customer_wrote")}</div>
          <div className="line-source-text" title={l.source.text}>{l.source.text}</div>
          <div className="line-match-label">{t("matched_product")}</div>
          <div className="text-[15px] font-semibold leading-snug">{l.final_name || l.parsed.name || <i className="text-red-800">{t("unreadable")}</i>}</div>
          {l.final_sku ? <div className="font-mono text-xs soft">SKU {l.final_sku}</div> : session.analyzed && <div className="text-xs font-semibold text-amber-800">{t("no_sku")}</div>}
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
          {session.analyzed && (l.match.sku ? <BandBadge band={l.match.band} score={l.match.match_score} /> : <BandBadge band="LOW" score={null} />)}
          {session.analyzed && <LineStatusBadge status={l.line_status} />}
          {session.analyzed && <StockBadge stock={l.stock} />}
          {l.stock.updated_at && <span className="text-[11px] soft">{t("updated", { time: fmtTime(l.stock.updated_at) })}</span>}
        </div>
        <div className="tline-amount">{amount != null ? fmtMoney(amount, "").trim() : "—"}</div>
      </div>
    );
  };

  const flagged = sorted.filter((l) => priority(l) <= 3);
  const clean = sorted.filter((l) => priority(l) > 3);

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
          <div className="tline-group text-amber-900">{t("group_attention", { n: flagged.length })}</div>
          {flagged.map((l, i) => row(l, i))}
          {clean.length > 0 && <div className="tline-group text-emerald-800">{t("group_ok", { n: clean.length })}</div>}
          {clean.map((l, i) => row(l, flagged.length + i))}
        </>
      ) : (
        sorted.map((l, i) => row(l, i))
      )}
    </>
  );
}
