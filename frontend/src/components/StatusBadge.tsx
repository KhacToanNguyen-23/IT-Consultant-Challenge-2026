import clsx from "clsx";
import { AlertTriangle, ArrowUpCircle, CheckCircle2, Eye, PackageX, HelpCircle } from "lucide-react";
import type { Band, Line, LineStatus } from "@/client/api";

const base = "inline-flex items-center gap-1 rounded-md border px-2 py-0.5 text-xs font-semibold whitespace-nowrap";

// SRS v2 §8 colour map — colour is never the only signal (icon + text always present)
export function BandBadge({ band, score }: { band: Band; score: number | null }) {
  if (band === "HIGH")
    return (
      <span className={clsx(base, "bg-emerald-50 border-emerald-500 text-emerald-900")}>
        <CheckCircle2 size={13} aria-hidden /> Khớp cao {score?.toFixed(2)}
      </span>
    );
  if (band === "REVIEW")
    return (
      <span className={clsx(base, "bg-green-50 border-green-400 text-green-900")}>
        <Eye size={13} aria-hidden /> Kiểm nhanh {score?.toFixed(2)}
      </span>
    );
  return (
    <span className={clsx(base, "bg-amber-50 border-amber-500 text-amber-950")}>
      <AlertTriangle size={13} aria-hidden /> Cần chọn {score != null ? score.toFixed(2) : ""}
    </span>
  );
}

export function StockBadge({ stock }: { stock: Line["stock"] }) {
  if (!stock.status) return <span className="text-xs text-slate-400">—</span>;
  if (stock.status === "IN_STOCK")
    return (
      <span className={clsx(base, "bg-emerald-50 border-emerald-500 text-emerald-900")}>
        <CheckCircle2 size={13} aria-hidden /> Còn {stock.on_hand}
      </span>
    );
  if (stock.status === "UNKNOWN")
    return (
      <span className={clsx(base, "bg-slate-50 border-slate-400 text-slate-700")}>
        <HelpCircle size={13} aria-hidden /> Không rõ tồn
      </span>
    );
  return (
    <span className={clsx(base, "bg-red-50 border-red-500 text-red-900")}>
      <PackageX size={13} aria-hidden /> {stock.status === "PARTIAL" ? `Thiếu một phần (${stock.on_hand})` : "Hết hàng"}
    </span>
  );
}

const LS: Record<LineStatus, { label: string; cls: string }> = {
  NEEDS_CLARIFICATION: { label: "Cần làm rõ", cls: "bg-amber-50 border-amber-500 text-amber-950" },
  MATCHED: { label: "Đã khớp", cls: "bg-slate-50 border-slate-300 text-slate-800" },
  UNIT_CONVERTED: { label: "Đã quy đổi", cls: "bg-slate-50 border-slate-300 text-slate-800" },
  SUBSTITUTE_PROPOSED: { label: "Đề xuất thay thế", cls: "bg-red-50 border-red-500 text-red-900" },
  CUSTOMER_ACCEPTED: { label: "Khách đồng ý thay", cls: "bg-emerald-50 border-emerald-500 text-emerald-900" },
};

export function LineStatusBadge({ status }: { status: LineStatus }) {
  const s = LS[status];
  return <span className={clsx(base, s.cls)}>{s.label}</span>;
}

export function RoundedBadge() {
  return (
    <span className={clsx(base, "bg-blue-50 border-blue-200 text-blue-900")}>
      <ArrowUpCircle size={13} aria-hidden /> Đã làm tròn lên
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

export function StatePill({ status }: { status: string }) {
  return <span className={clsx(base, QS[status] || "bg-slate-100 text-slate-700 border-slate-300")}>{status}</span>;
}

export function AttributeChips({ chips }: { chips: Line["chips"] }) {
  if (!chips.length) return null;
  return (
    <div className="mt-1 flex flex-wrap gap-1">
      {chips.map((c) => (
        <span
          key={c.attr}
          title={c.tone === "emerald" ? "Khớp điều khách viết" : c.tone === "slate" ? "Khách không nêu" : "Lệch với yêu cầu"}
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
