"use client";

import { Fragment, useMemo, useRef, useState } from "react";
import clsx from "clsx";
import { ChevronDown, ChevronRight, Search, Loader2, Check, X } from "lucide-react";
import { api, ApiError, fmtMoney, fmtTime, UNIT_LABEL, type Line, type SessionView } from "@/client/api";
import { AttributeChips, BandBadge, LineStatusBadge, RoundedBadge, StockBadge } from "./StatusBadge";

const ATTR_LABEL: Record<string, string> = {
  cross_section_mm: "tiết diện",
  strength_grade: "cấp cường độ (C18/C24…)",
  thickness_mm: "độ dày",
  moisture_resistant: "loại thường/vådrum",
  bag_weight_kg: "trọng lượng bao",
  product_type: "loại (xi măng/vữa)",
  treatment: "xử lý gỗ",
  length_m: "chiều dài",
  brand: "thương hiệu",
};

function priority(l: Line): number {
  if (l.line_status === "NEEDS_CLARIFICATION") return 0;
  if (l.line_status === "SUBSTITUTE_PROPOSED") return 1;
  if (l.stock.status === "OUT_OF_STOCK" || l.stock.status === "PARTIAL") return 2;
  if (l.match.band !== "HIGH") return 3;
  return 4;
}

function rowTone(l: Line) {
  if (l.line_status === "NEEDS_CLARIFICATION") return "bg-amber-50/70 border-l-amber-500";
  if (l.line_status === "SUBSTITUTE_PROPOSED" || ((l.stock.status === "OUT_OF_STOCK" || l.stock.status === "PARTIAL") && l.line_status !== "CUSTOMER_ACCEPTED"))
    return "bg-red-50/60 border-l-red-500";
  if (l.line_status === "CUSTOMER_ACCEPTED") return "bg-emerald-50/50 border-l-emerald-500";
  if (l.match.band === "REVIEW") return "bg-green-50/40 border-l-green-400";
  return "bg-white border-l-emerald-500";
}

export default function ReviewTable({ session, onChange }: { session: SessionView; onChange: (v: SessionView) => void }) {
  const sorted = useMemo(
    () => [...session.lines].sort((a, b) => priority(a) - priority(b) || a.line_no - b.line_no),
    [session.lines]
  );
  const [open, setOpen] = useState<number | null>(() => sorted.find((l) => priority(l) <= 1)?.line_no ?? null);
  const rowRefs = useRef<Record<number, HTMLTableRowElement | null>>({});
  const locked = session.locked;

  const onRowKey = (e: React.KeyboardEvent, idx: number, l: Line) => {
    if (e.target !== e.currentTarget) return;
    if (e.key === "ArrowDown" || e.key === "ArrowUp") {
      e.preventDefault();
      const next = sorted[idx + (e.key === "ArrowDown" ? 1 : -1)];
      if (next) rowRefs.current[next.line_no]?.focus();
    } else if (e.key === "Enter") {
      e.preventDefault();
      setOpen(open === l.line_no ? null : l.line_no);
    } else if (e.key === "Escape") {
      setOpen(null);
    }
  };

  const exceptions = sorted.filter((l) => priority(l) <= 3).length;

  return (
    <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white shadow-sm">
      <div className="flex flex-wrap items-center gap-3 border-b border-slate-200 px-4 py-2 text-sm">
        <span className="font-semibold">{session.lines.length} dòng</span>
        <span className="text-slate-500">·</span>
        <span className={clsx(exceptions ? "font-semibold text-amber-800" : "text-emerald-700")}>{exceptions} dòng cần xem (xếp lên đầu)</span>
        <span className="ml-auto text-xs text-slate-500">↑↓ chọn dòng · Enter mở/đóng · Esc đóng</span>
      </div>
      <table className="w-full min-w-[1100px] text-sm">
        <thead className="bg-slate-50 text-left text-xs uppercase tracking-wide text-slate-500">
          <tr>
            <th className="w-8 px-2 py-2" />
            <th className="px-2 py-2">#</th>
            <th className="px-2 py-2">Khách ghi / đã đọc</th>
            <th className="px-2 py-2">SL yêu cầu → đơn vị bán</th>
            <th className="px-2 py-2">SKU đề xuất</th>
            <th className="px-2 py-2">Match score</th>
            <th className="px-2 py-2">Trạng thái</th>
            <th className="px-2 py-2">Tồn (on-hand)</th>
            <th className="px-2 py-2">Xử lý</th>
          </tr>
        </thead>
        <tbody>
          {sorted.map((l, idx) => (
            <Fragment key={l.line_id}>
              <tr
                ref={(el) => {
                  rowRefs.current[l.line_no] = el;
                }}
                tabIndex={0}
                onKeyDown={(e) => onRowKey(e, idx, l)}
                onClick={() => setOpen(open === l.line_no ? null : l.line_no)}
                aria-expanded={open === l.line_no}
                className={clsx(
                  "cursor-pointer border-b border-l-4 border-slate-100 align-top focus:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-blue-600",
                  rowTone(l)
                )}
              >
                <td className="px-2 py-2.5 text-slate-400">{open === l.line_no ? <ChevronDown size={16} /> : <ChevronRight size={16} />}</td>
                <td className="px-2 py-2.5 tabular text-slate-500">{l.line_no}</td>
                <td className="max-w-[260px] px-2 py-2.5">
                  <div className="font-mono text-xs text-slate-500">{l.source.text}</div>
                  <div className="font-medium">{l.parsed.name || <i className="text-red-700">không đọc được</i>}</div>
                  {l.parsed.warnings.includes("n_x_l_review") && <div className="text-xs text-amber-800">N × L: {l.conversion.requested}</div>}
                </td>
                <td className="px-2 py-2.5 tabular">
                  <div>
                    {l.parsed.quantity ?? "?"} {l.parsed.unit ? UNIT_LABEL[l.parsed.unit] || l.parsed.unit : <span className="text-amber-800">{l.parsed.unit_raw || "đơn vị?"}</span>}
                  </div>
                  {l.conversion.selling_quantity != null ? (
                    <div className="font-semibold">
                      → {l.conversion.selling_quantity} × {l.conversion.selling_unit}
                    </div>
                  ) : (
                    session.analyzed && <div className="text-xs text-amber-800">{l.conversion.blocked_reason}</div>
                  )}
                  {l.conversion.formula && <div className="text-xs text-slate-500">{l.conversion.formula}</div>}
                  {l.conversion.rounded && <RoundedBadge />}
                </td>
                <td className="max-w-[300px] px-2 py-2.5">
                  {l.final_sku ? (
                    <>
                      {l.line_status === "CUSTOMER_ACCEPTED" && <div className="text-xs text-slate-500 line-through">{l.match.sku}</div>}
                      <div className="font-mono text-xs text-slate-500">{l.final_sku}</div>
                      <div className="font-medium">{l.final_name}</div>
                      <AttributeChips chips={l.chips} />
                    </>
                  ) : (
                    <span className="text-amber-800">Chưa có SKU</span>
                  )}
                </td>
                <td className="px-2 py-2.5">{session.analyzed && (l.match.sku ? <BandBadge band={l.match.band} score={l.match.match_score} /> : <BandBadge band="LOW" score={null} />)}</td>
                <td className="px-2 py-2.5">{session.analyzed && <LineStatusBadge status={l.line_status} />}</td>
                <td className="px-2 py-2.5">
                  <StockBadge stock={l.stock} />
                  {l.stock.updated_at && <div className="mt-0.5 text-[11px] text-slate-500">cập nhật {fmtTime(l.stock.updated_at)}</div>}
                </td>
                <td className="px-2 py-2.5 text-xs">
                  <ActionHint l={l} />
                </td>
              </tr>
              {open === l.line_no && (
                <tr className="border-b border-slate-200 bg-slate-50/80">
                  <td colSpan={9} className="px-4 py-4">
                    <LineDetail session={session} line={l} locked={locked} onChange={onChange} onClose={() => setOpen(null)} />
                  </td>
                </tr>
              )}
            </Fragment>
          ))}
        </tbody>
      </table>
      <p className="border-t border-slate-200 px-4 py-2 text-xs text-slate-500">
        Tồn tham khảo (on-hand), cần xác nhận trước khi hứa hàng. Match score là điểm xếp hạng [0–1], không phải xác suất.
      </p>
    </div>
  );
}

function ActionHint({ l }: { l: Line }) {
  if (l.line_status === "NEEDS_CLARIFICATION") {
    const missing = (l.match.reasons as Line["match"]["reasons"] & { missing?: string[] })?.missing || [];
    if (!l.parsed.name) return <span className="font-semibold text-amber-900">Nhập tay / tìm SKU</span>;
    if (l.conversion.blocked_reason) return <span className="font-semibold text-amber-900">Làm rõ SL/đơn vị</span>;
    if (missing.length) return <span className="font-semibold text-amber-900">Hỏi khách: {missing.map((m) => ATTR_LABEL[m] || m).join(", ")}</span>;
    return <span className="font-semibold text-amber-900">Chọn SKU</span>;
  }
  if (l.line_status === "SUBSTITUTE_PROPOSED") return <span className="font-semibold text-red-900">Hỏi khách: {l.alternatives.length} SKU thay thế</span>;
  if (l.line_status === "CUSTOMER_ACCEPTED") return <span className="text-emerald-800">Đã thay thế (khách đồng ý)</span>;
  if (l.fulfillment_action === "backorder")
    return <span className="text-red-900">{l.substitution.rejection_reason ? `Khách từ chối thay: ${l.substitution.rejection_reason}` : "Không có thay thế an toàn → chờ hàng"}</span>;
  return <span className="text-slate-500">—</span>;
}

// ---------------- detail panel ----------------
function LineDetail({ session, line, locked, onChange, onClose }: { session: SessionView; line: Line; locked: boolean; onChange: (v: SessionView) => void; onClose: () => void }) {
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const run = async (fn: () => Promise<SessionView>) => {
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

  const reasons = line.match.reasons as Line["match"]["reasons"] & { missing?: string[]; ambiguous?: boolean };

  return (
    <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.2fr)]" onClick={(e) => e.stopPropagation()}>
      <div className="space-y-3">
        <ParseEditor session={session} line={line} locked={locked} run={run} />
        {session.analyzed && line.match.sku && (
          <div className="rounded-md border border-slate-200 bg-white p-3 text-xs">
            <div className="mb-1 font-semibold text-slate-700">Vì sao gợi ý này?</div>
            {reasons?.matched?.length ? <div>✓ Khớp: {reasons.matched.map((m) => ATTR_LABEL[m] || m).join(", ")}</div> : null}
            {reasons?.mismatched?.length ? <div className="text-red-800">≠ Khác (tùy chọn, đã trừ điểm): {reasons.mismatched.map((m) => ATTR_LABEL[m] || m).join(", ")}</div> : null}
            {reasons?.missing?.length ? <div className="text-amber-900">? Khách chưa nêu (bắt buộc): {reasons.missing.map((m) => ATTR_LABEL[m] || m).join(", ")} — không tự đoán</div> : null}
            {reasons?.ambiguous && <div className="text-amber-900">Hai ứng viên gần điểm nhau (&lt;0.05) → giới hạn 0.89, cần kiểm.</div>}
            <div className="mt-1 text-slate-500">SKU sai thuộc tính bắt buộc (vd. C18 vs C24) bị loại, không bao giờ được tự chọn.</div>
          </div>
        )}
      </div>

      <div className="space-y-3">
        {err && <p role="alert" className="rounded-md border border-red-300 bg-red-50 px-3 py-2 text-sm text-red-900">{err}</p>}

        {session.analyzed && line.line_status === "SUBSTITUTE_PROPOSED" && !locked && (
          <Alternatives line={line} busy={busy} onAccept={(sku) => select(sku, "SUBSTITUTION_ACCEPTED")} onReject={(reason) => select(line.match.sku!, "SUBSTITUTION_REJECTED", reason)} />
        )}

        {session.analyzed && line.line_status === "CUSTOMER_ACCEPTED" && !locked && (
          <div className="rounded-md border border-emerald-300 bg-emerald-50 p-3 text-sm">
            Khách đã đồng ý thay <b>{line.match.sku}</b> → <b>{line.final_sku}</b> ({fmtTime(line.substitution.accepted_at)}).
            <button className="ml-2 text-xs font-semibold text-red-800 underline" disabled={busy} onClick={() => select(line.match.sku!, "SUBSTITUTION_REJECTED", "Khách đổi ý")}>
              Hoàn tác
            </button>
          </div>
        )}

        {session.analyzed && !locked && line.match.candidates.length > 0 && line.line_status === "NEEDS_CLARIFICATION" && (
          <div className="rounded-md border border-amber-300 bg-white p-3">
            <div className="mb-2 text-sm font-semibold">Ứng viên (≤3) — chọn sau khi hỏi khách</div>
            <ul className="space-y-1.5">
              {line.match.candidates.map((c) => (
                <li key={c.sku} className="flex items-center gap-2 text-sm">
                  <BandBadge band={c.band} score={c.score} />
                  <span className="font-mono text-xs text-slate-500">{c.sku}</span>
                  <span className="flex-1">{c.name}</span>
                  <button
                    disabled={busy}
                    onClick={() => select(c.sku, c.sku === line.match.sku ? "SKU_KEPT" : "SKU_EDITED")}
                    className="rounded border border-slate-300 bg-white px-2 py-0.5 text-xs font-semibold hover:bg-slate-100 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-600"
                  >
                    Chọn
                  </button>
                </li>
              ))}
            </ul>
          </div>
        )}

        {session.analyzed && !locked && (
          <CatalogSearch
            initial={line.parsed.name || ""}
            busy={busy}
            degraded={session.ai_degraded}
            onPick={(sku) => select(sku, sku === line.match.sku ? "SKU_KEPT" : "SKU_EDITED")}
          />
        )}
        <div className="flex justify-end">
          <button onClick={onClose} className="text-xs text-slate-500 hover:underline">
            Đóng (Esc)
          </button>
        </div>
      </div>
    </div>
  );
}

function ParseEditor({ session, line, locked, run }: { session: SessionView; line: Line; locked: boolean; run: (fn: () => Promise<SessionView>) => Promise<void> }) {
  const [name, setName] = useState(line.parsed.name || "");
  const [qty, setQty] = useState(line.parsed.quantity?.toString() || "");
  const [unit, setUnit] = useState(line.parsed.unit || "");
  const dirty = name !== (line.parsed.name || "") || qty !== (line.parsed.quantity?.toString() || "") || unit !== (line.parsed.unit || "");
  const save = () =>
    run(() =>
      api(`/sessions/${session.session_id}/lines/${line.line_no}`, {
        method: "PATCH",
        json: {
          item_text: name !== (line.parsed.name || "") ? name : null,
          requested_qty: qty && Number(qty) !== line.parsed.quantity ? Number(qty.replace(",", ".")) : null,
          requested_unit: unit && unit !== line.parsed.unit ? unit : null,
        },
      })
    );
  return (
    <form
      className="rounded-md border border-slate-200 bg-white p-3"
      onSubmit={(e) => {
        e.preventDefault();
        if (dirty) save();
      }}
    >
      <div className="mb-2 text-sm font-semibold">Sửa dòng đã đọc</div>
      <div className="font-mono text-xs text-slate-500">Nguồn: {line.source.text}</div>
      <div className="mt-2 grid grid-cols-[1fr_90px_130px] gap-2">
        <input disabled={locked} aria-label="Tên vật tư" value={name} onChange={(e) => setName(e.target.value)} className="rounded border border-slate-300 px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-blue-600" />
        <input disabled={locked} aria-label="Số lượng" inputMode="decimal" value={qty} onChange={(e) => setQty(e.target.value)} className="rounded border border-slate-300 px-2 py-1 text-sm tabular focus:outline-none focus:ring-2 focus:ring-blue-600" />
        <select disabled={locked} aria-label="Đơn vị" value={unit} onChange={(e) => setUnit(e.target.value)} className="rounded border border-slate-300 px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-blue-600">
          <option value="">— đơn vị —</option>
          {Object.entries(UNIT_LABEL).map(([k, v]) => (
            <option key={k} value={k}>
              {v} ({k})
            </option>
          ))}
        </select>
      </div>
      {line.parsed.unit_raw && !line.parsed.unit && <div className="mt-1 text-xs text-amber-800">Đơn vị khách ghi “{line.parsed.unit_raw}” chưa có trong từ điển — chọn đơn vị đúng.</div>}
      {!locked && (
        <div className="mt-2 flex justify-end">
          <button type="submit" disabled={!dirty} className="rounded bg-slate-900 px-3 py-1 text-xs font-semibold text-white disabled:opacity-40">
            Lưu {session.analyzed ? "& phân tích lại dòng" : ""}
          </button>
        </div>
      )}
    </form>
  );
}

function Alternatives({ line, busy, onAccept, onReject }: { line: Line; busy: boolean; onAccept: (sku: string) => void; onReject: (reason: string) => void }) {
  const [reason, setReason] = useState("");
  return (
    <div className="rounded-md border border-red-300 bg-white p-3">
      <div className="text-sm font-semibold text-red-900">
        {line.stock.status === "PARTIAL" ? `Chỉ còn ${line.stock.on_hand}, cần ${line.conversion.selling_quantity}` : "Hết hàng tại cửa hàng"} — thay thế an toàn (đủ tồn, thông số bằng/tốt hơn):
      </div>
      <ul className="mt-2 space-y-2">
        {line.alternatives.map((a) => (
          <li key={a.sku} className="rounded border border-slate-200 p-2 text-sm">
            <div className="flex flex-wrap items-center gap-2">
              <span className="font-mono text-xs text-slate-500">{a.sku}</span>
              <span className="font-medium">{a.name}</span>
              {a.different_grade && <span className="rounded bg-blue-50 px-1.5 text-[11px] text-blue-900">cấp cao hơn</span>}
              <span className="ml-auto text-xs tabular">
                còn {a.on_hand} · {a.needed_quantity} × {a.selling_unit} · Δ {a.total_price_delta >= 0 ? "+" : ""}
                {fmtMoney(a.total_price_delta, a.currency)}
              </span>
            </div>
            <div className="mt-1 text-xs text-slate-500">{a.reasons.join(" · ")}</div>
            <button
              disabled={busy}
              onClick={() => onAccept(a.sku)}
              className="mt-2 inline-flex items-center gap-1 rounded bg-emerald-700 px-2.5 py-1 text-xs font-semibold text-white hover:bg-emerald-800 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-600"
            >
              <Check size={14} /> Khách đồng ý thay
            </button>
          </li>
        ))}
      </ul>
      <div className="mt-3 flex gap-2">
        <input value={reason} onChange={(e) => setReason(e.target.value)} placeholder="Lý do khách từ chối (bắt buộc)" className="flex-1 rounded border border-slate-300 px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-blue-600" />
        <button
          disabled={busy || !reason.trim()}
          onClick={() => onReject(reason)}
          className="inline-flex items-center gap-1 rounded border border-red-400 bg-white px-2.5 py-1 text-xs font-semibold text-red-900 hover:bg-red-50 disabled:opacity-40"
        >
          <X size={14} /> Khách từ chối
        </button>
      </div>
      <p className="mt-2 text-[11px] text-slate-500">SKU cuối chỉ đổi sau khi khách đồng ý. Từ chối → giữ SKU gốc, ghi chờ hàng.</p>
    </div>
  );
}

function CatalogSearch({ initial, busy, degraded, onPick }: { initial: string; busy: boolean; degraded: boolean; onPick: (sku: string) => void }) {
  const [q, setQ] = useState(initial);
  const [items, setItems] = useState<{ sku: string; name: string; unit_price: number; currency: string; selling_unit: string }[] | null>(null);
  const [loading, setLoading] = useState(false);
  const search = async () => {
    setLoading(true);
    try {
      setItems((await api(`/catalog/search?q=${encodeURIComponent(q)}&limit=8`)).items);
    } finally {
      setLoading(false);
    }
  };
  return (
    <div className={clsx("rounded-md border bg-white p-3", degraded ? "border-amber-600" : "border-slate-200")}>
      <div className="mb-2 text-sm font-semibold">{degraded ? "AI lỗi — tìm SKU thủ công" : "Tìm SKU khác trong catalog"}</div>
      <form
        className="flex gap-2"
        onSubmit={(e) => {
          e.preventDefault();
          search();
        }}
      >
        <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="vd. 45x95 c24, gips 12.5" className="flex-1 rounded border border-slate-300 px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-blue-600" />
        <button type="submit" className="inline-flex items-center gap-1 rounded border border-slate-300 px-2.5 py-1 text-xs font-semibold hover:bg-slate-50">
          {loading ? <Loader2 size={14} className="animate-spin" /> : <Search size={14} />} Tìm
        </button>
      </form>
      {items && (
        <ul className="mt-2 max-h-52 space-y-1 overflow-auto">
          {items.length === 0 && <li className="text-xs text-slate-500">Không tìm thấy — thử từ khoá khác.</li>}
          {items.map((i) => (
            <li key={i.sku} className="flex items-center gap-2 text-sm">
              <span className="font-mono text-xs text-slate-500">{i.sku}</span>
              <span className="flex-1">{i.name}</span>
              <span className="text-xs text-slate-500 tabular">{fmtMoney(i.unit_price, i.currency)}</span>
              <button disabled={busy} onClick={() => onPick(i.sku)} className="rounded border border-slate-300 px-2 py-0.5 text-xs font-semibold hover:bg-slate-100">
                Chọn
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
