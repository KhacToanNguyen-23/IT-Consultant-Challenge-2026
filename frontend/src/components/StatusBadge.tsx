"use client";

import clsx from "clsx";
import { AlertTriangle, ArrowUpCircle, CheckCircle2, Eye, PackageX, HelpCircle } from "lucide-react";
import type { Band, Line, LineStatus } from "@/client/api";
import { useI18n, type Key } from "@/client/i18n";

const base = "inline-flex items-center gap-1 rounded-sm border px-1.5 py-0.5 text-xs font-semibold whitespace-nowrap";

// SRS v2 §8 colour map — colour is never the only signal (icon + text always present)
export function BandBadge({ band, score }: { band: Band; score: number | null }) {
  const { t } = useI18n();
  if (band === "HIGH")
    return (
      <span className={clsx(base, "bg-emerald-50 border-emerald-500 text-emerald-900")}>
        <CheckCircle2 size={13} aria-hidden /> {t("band_high")} {score?.toFixed(2)}
      </span>
    );
  if (band === "REVIEW")
    return (
      <span className={clsx(base, "bg-green-50 border-green-400 text-green-900")}>
        <Eye size={13} aria-hidden /> {t("band_review")} {score?.toFixed(2)}
      </span>
    );
  return (
    <span className={clsx(base, "bg-amber-50 border-amber-500 text-amber-950")}>
      <AlertTriangle size={13} aria-hidden /> {t("band_low")} {score != null ? score.toFixed(2) : ""}
    </span>
  );
}

export function StockBadge({ stock }: { stock: Line["stock"] }) {
  const { t } = useI18n();
  if (!stock.status) return <span className="text-xs text-slate-400">—</span>;
  if (stock.status === "IN_STOCK")
    return (
      <span className={clsx(base, "bg-emerald-50 border-emerald-500 text-emerald-900")}>
        <CheckCircle2 size={13} aria-hidden /> {t("stock_in", { n: stock.on_hand ?? "" })}
      </span>
    );
  if (stock.status === "UNKNOWN")
    return (
      <span className={clsx(base, "bg-slate-50 border-slate-400 text-slate-700")}>
        <HelpCircle size={13} aria-hidden /> {t("stock_unknown")}
      </span>
    );
  return (
    <span className={clsx(base, "bg-red-50 border-red-500 text-red-900")}>
      <PackageX size={13} aria-hidden /> {stock.status === "PARTIAL" ? t("stock_partial", { n: stock.on_hand ?? 0 }) : t("stock_out")}
    </span>
  );
}

const LS_CLS: Record<LineStatus, string> = {
  NEEDS_CLARIFICATION: "bg-amber-50 border-amber-500 text-amber-950",
  MATCHED: "bg-slate-50 border-slate-300 text-slate-800",
  UNIT_CONVERTED: "bg-slate-50 border-slate-300 text-slate-800",
  SUBSTITUTE_PROPOSED: "bg-red-50 border-red-500 text-red-900",
  CUSTOMER_ACCEPTED: "bg-emerald-50 border-emerald-500 text-emerald-900",
};

export function LineStatusBadge({ status }: { status: LineStatus }) {
  const { t } = useI18n();
  return <span className={clsx(base, LS_CLS[status])}>{t(`ls_${status}`)}</span>;
}

export function RoundedBadge() {
  const { t } = useI18n();
  return (
    <span className={clsx(base, "bg-blue-50 border-blue-200 text-blue-900")}>
      <ArrowUpCircle size={13} aria-hidden /> {t("rounded")}
    </span>
  );
}

const QS: Record<string, string> = {
  SAVED: "bg-slate-100 text-slate-800 border-slate-300",
  SENT: "bg-blue-50 text-blue-900 border-blue-300",
  PREPARING: "bg-violet-50 text-violet-900 border-violet-300",
  CONFIRMED: "bg-emerald-50 text-emerald-900 border-emerald-500",
  EXPIRED: "bg-amber-50 text-amber-950 border-amber-500",
  CANCELLED: "bg-red-50 text-red-900 border-red-400",
  POS_ACCEPTED: "bg-emerald-50 text-emerald-900 border-emerald-500",
  NEEDS_MANUAL: "bg-amber-50 text-amber-950 border-amber-500",
  REVIEW_REQUIRED: "bg-amber-50 text-amber-950 border-amber-500",
  READY_TO_CONFIRM: "bg-emerald-50 text-emerald-900 border-emerald-500",
};

const STATE_LABELS: Record<string, Key> = {
  DRAFT: "state_draft",
  PARSED: "state_read",
  ANALYZED: "state_analyzed",
  REVIEW_REQUIRED: "state_review_required",
  READY_TO_CONFIRM: "state_ready",
  SAVED: "state_saved",
  SENT: "state_sent",
  PREPARING: "state_preparing",
  CONFIRMED: "state_confirmed",
  POS_ACCEPTED: "state_pos_accepted",
  NEEDS_MANUAL: "state_needs_manual",
  SENT_OR_EXPORTED: "state_exported",
  EXPIRED: "state_expired",
  CANCELLED: "state_cancelled",
};

/** Show readable state labels while retaining the exact state code as a tooltip for audit/demo checks. */
export function StatePill({ status }: { status: string }) {
  const { t } = useI18n();
  const key = STATE_LABELS[status];
  const label = key ? t(key) : status;
  return <span role="status" title={status} aria-label={`${label} (${status})`} className={clsx(base, QS[status] || "bg-slate-100 text-slate-700 border-slate-300")}>{label}</span>;
}

export function AttributeChips({ chips }: { chips: Line["chips"] }) {
  const { t } = useI18n();
  if (!chips.length) return null;
  return (
    <div className="mt-1 flex flex-wrap gap-1">
      {chips.map((c) => (
        <span
          key={c.attr}
          title={c.tone === "emerald" ? t("chip_match") : c.tone === "slate" ? t("chip_unstated") : t("chip_diff")}
          className={clsx(
            "rounded px-1.5 py-0.5 text-[11px] font-medium border",
            c.tone === "emerald" && "bg-emerald-50 border-emerald-300 text-emerald-900",
            c.tone === "slate" && "bg-slate-50 border-slate-300 text-slate-600",
            c.tone === "red" && "bg-red-50 border-red-400 text-red-900"
          )}
        >
          {c.tone === "red" ? "≠ " : c.tone === "emerald" ? "✓ " : ""}
          {c.value}
        </span>
      ))}
    </div>
  );
}
