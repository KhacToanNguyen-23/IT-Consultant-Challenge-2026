"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import clsx from "clsx";
import { AlertTriangle, CheckCircle2, Download, FileText, Loader2, Lock, Sparkles } from "lucide-react";
import { api, ApiError, fileUrl, type Customer, type SessionView } from "@/client/api";
import ReviewTable from "@/components/ReviewTable";
import { StatePill } from "@/components/StatusBadge";

function plusDays(n: number) {
  const d = new Date();
  d.setDate(d.getDate() + n);
  return d.toISOString().slice(0, 10);
}

export default function SessionPage({ params }: { params: { id: string } }) {
  const router = useRouter();
  const [s, setS] = useState<SessionView | null>(null);
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [clientId, setClientId] = useState("");
  const [validUntil, setValidUntil] = useState(plusDays(7));
  const [showSource, setShowSource] = useState(true);

  const load = useCallback(async () => {
    try {
      const v = await api<SessionView>(`/sessions/${params.id}`);
      setS(v);
      setClientId((c) => c || v.client_id || "");
    } catch (e) {
      setError(e instanceof ApiError ? e.message : String(e));
    }
  }, [params.id]);

  useEffect(() => {
    load();
    api<{ items: Customer[] }>("/customers").then((r) => setCustomers(r.items)).catch(() => {});
    const h = () => load();
    window.addEventListener("sitedesk:health", h);
    return () => window.removeEventListener("sitedesk:health", h);
  }, [load]);

  const act = async (key: string, fn: () => Promise<void>) => {
    setBusy(key);
    setError(null);
    try {
      await fn();
    } catch (e) {
      if (e instanceof ApiError) {
        const lines = (e.details?.line_nos as number[] | undefined)?.join(", ");
        setError(e.message + (lines ? ` (dòng ${lines})` : ""));
      } else setError(String(e));
    } finally {
      setBusy(null);
    }
  };

  if (!s) return <div className="py-20 text-center text-slate-500">{error || <Loader2 className="mx-auto animate-spin" />}</div>;

  const isEmail = s.input_type === "email";
  const walkIn = customers.find((c) => c.customer_type === "B2C_WalkIn")?.client_id;
  const effectiveClient = clientId || walkIn || "";
  const canConfirmQuote = !s.quote || s.quote.status === "PREPARING";
  const t = s.stage_timings_ms;

  return (
    <div className="space-y-4">
      {/* header */}
      <div className="flex flex-wrap items-end gap-3">
        <div>
          <div className="text-xs text-slate-500">
            <Link href="/" className="hover:underline">
              ← Danh sách mới
            </Link>{" "}
            · {isEmail ? "Luồng 2 · Email báo giá" : "Luồng 1 · Tại quầy"}
          </div>
          <h1 className="text-xl font-bold">
            {s.order_session_id} <StatePill status={s.status} />
          </h1>
        </div>
        <Stepper analyzed={s.analyzed} locked={s.locked} blockers={s.blockers.length} />
        {s.analyzed && typeof t.total_ms === "number" && (
          <div className="ml-auto text-right text-xs text-slate-500 tabular" title="Thời gian đo thật từ backend (FR-030)">
            Phân tích {t.lines as number} dòng: <b className="text-slate-800">{((t.total_ms as number) / 1000).toFixed(2)} s</b>
            <div>
              match {t.match_ms}ms · tồn {t.stock_ms}ms · quy tắc {t.rules_convert_alternatives_ms}ms
            </div>
          </div>
        )}
      </div>

      {s.ai_degraded && (
        <div role="status" className="flex items-center gap-2 rounded-md border border-amber-600 bg-amber-100 px-3 py-2 text-sm text-amber-950">
          <AlertTriangle size={16} /> AI lỗi — đang chạy chế độ quy tắc + tìm thủ công. Quầy vẫn Confirm được.
        </div>
      )}
      {s.lines.some((l) => l.stock.status === "UNKNOWN") && (
        <div role="status" className="flex items-center gap-2 rounded-md border border-amber-600 bg-amber-50 px-3 py-2 text-sm text-amber-950">
          <AlertTriangle size={16} /> Không đọc được tồn kho từ POS (simulated) — không hiển thị/đoán tồn.
        </div>
      )}
      {error && (
        <p role="alert" className="rounded-md border border-red-300 bg-red-50 px-3 py-2 text-sm text-red-900">
          {error}
        </p>
      )}

      {/* source panel */}
      {s.masked_source && (
        <div className="rounded-lg border border-slate-200 bg-white shadow-sm">
          <button onClick={() => setShowSource(!showSource)} className="flex w-full items-center gap-2 px-4 py-2 text-left text-sm font-semibold">
            <FileText size={16} /> Nguồn đã che email/điện thoại · Đã đọc {s.read_line_count} dòng
            <span className="ml-auto text-xs font-normal text-slate-500">{showSource ? "ẩn" : "hiện"}</span>
          </button>
          {showSource && (
            <div className="border-t border-slate-200 px-4 py-3">
              <pre className="max-h-48 overflow-auto whitespace-pre-wrap font-mono text-xs text-slate-700">{s.masked_source}</pre>
              <p className="mt-2 text-[11px] text-slate-500">
                Chỉ email & số điện thoại được che bằng regex; tên/địa chỉ trong văn bản tự do chưa được đảm bảo che. Nguồn bị xoá sau khi Confirm.
              </p>
            </div>
          )}
        </div>
      )}

      {!s.analyzed && (
        <div className="flex flex-wrap items-center gap-3 rounded-lg border border-blue-200 bg-blue-50 px-4 py-3 text-sm">
          <span>
            Bước 2/4 · Kiểm tra {s.read_line_count} dòng đã đọc (bấm vào dòng để sửa tên/SL/đơn vị), rồi phân tích. Dòng không đọc được vẫn được giữ lại.
          </span>
          <button
            onClick={() => act("analyze", async () => setS(await api(`/sessions/${s.session_id}/analyze`, { method: "POST", json: { language_hint: "DA" } })))}
            disabled={!!busy}
            className="ml-auto inline-flex items-center gap-2 rounded-md bg-slate-900 px-4 py-2 font-semibold text-white hover:bg-slate-800 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-600 disabled:opacity-60"
          >
            {busy === "analyze" ? <Loader2 size={16} className="animate-spin" /> : <Sparkles size={16} />} Phân tích (Analyze)
          </button>
        </div>
      )}

      <ReviewTable session={s} onChange={setS} />

      {/* footer: confirm / quote */}
      {s.locked ? (
        <ConfirmResult s={s} />
      ) : (
        s.analyzed && (
          <div className="grid gap-4 lg:grid-cols-2">
            <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
              <h2 className="font-semibold">Bước 4/4 · Xác nhận đơn {s.quote && `(báo giá ${s.quote.quote_id})`}</h2>
              <label className="mt-3 block text-sm">
                Khách hàng (Client ID)
                <select
                  value={effectiveClient}
                  onChange={(e) => setClientId(e.target.value)}
                  disabled={!!s.quote}
                  className="mt-1 block w-full rounded border border-slate-300 px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-600"
                >
                  {customers.map((c) => (
                    <option key={c.client_id} value={c.client_id}>
                      {c.client_id} · {c.customer_type === "B2B" ? `B2B · ${c.discount_tier}` : "Khách lẻ (walk-in)"}
                    </option>
                  ))}
                </select>
              </label>
              {s.blockers.length > 0 && (
                <div className="mt-3 rounded-md border border-amber-400 bg-amber-50 p-2 text-sm text-amber-950">
                  <b>Chưa Confirm được — còn {s.blockers.length} dòng:</b>
                  <ul className="mt-1 list-disc pl-5">
                    {s.blockers.map((b) => (
                      <li key={b.line_no}>
                        Dòng {b.line_no}: {b.reason}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              {!canConfirmQuote && (
                <p className="mt-3 rounded-md border border-violet-300 bg-violet-50 p-2 text-sm text-violet-900">
                  Đơn này thuộc báo giá {s.quote!.quote_id} ({s.quote!.status}). Cần ghi nhận khách xác nhận và <b>Prepare</b> trước khi Confirm.{" "}
                  <Link className="font-semibold underline" href={`/quotes/${s.quote!.quote_id}`}>
                    Mở báo giá →
                  </Link>
                </p>
              )}
              <button
                disabled={!!busy || s.blockers.length > 0 || !canConfirmQuote || !effectiveClient}
                onClick={() =>
                  act("confirm", async () => {
                    await api(`/sessions/${s.session_id}/confirm`, {
                      method: "POST",
                      json: { client_id: effectiveClient },
                      headers: { "Idempotency-Key": s.order_session_id },
                    });
                    await load();
                  })
                }
                className="mt-4 inline-flex w-full items-center justify-center gap-2 rounded-md bg-emerald-700 px-4 py-2.5 font-semibold text-white hover:bg-emerald-800 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-600 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:bg-slate-300"
              >
                {busy === "confirm" ? <Loader2 size={16} className="animate-spin" /> : <CheckCircle2 size={16} />} Confirm & gửi POS
              </button>
              <p className="mt-2 text-xs text-slate-500">POS lỗi → tự xuất CSV cùng mã tham chiếu. Sau Confirm đơn chỉ đọc.</p>
            </div>

            {!s.quote ? (
              <div className={clsx("rounded-lg border bg-white p-4 shadow-sm", isEmail ? "border-violet-300 ring-1 ring-violet-200" : "border-slate-200")}>
                <h2 className="font-semibold">Lưu thành báo giá (Pre-order)</h2>
                <p className="mt-1 text-xs text-slate-500">
                  Chụp giá & tồn tại thời điểm lưu. Báo giá <b>không giữ chỗ</b> hàng. Cần làm rõ hết dòng vàng trước khi lưu.
                </p>
                <div className="mt-3 grid grid-cols-2 gap-3 text-sm">
                  <label>
                    Khách hàng
                    <select value={effectiveClient} onChange={(e) => setClientId(e.target.value)} className="mt-1 block w-full rounded border border-slate-300 px-2 py-1.5 focus:outline-none focus:ring-2 focus:ring-blue-600">
                      {customers.map((c) => (
                        <option key={c.client_id} value={c.client_id}>
                          {c.client_id} · {c.discount_tier}
                        </option>
                      ))}
                    </select>
                  </label>
                  <label>
                    Hiệu lực đến
                    <input type="date" value={validUntil} min={plusDays(0)} onChange={(e) => setValidUntil(e.target.value)} className="mt-1 block w-full rounded border border-slate-300 px-2 py-1.5 focus:outline-none focus:ring-2 focus:ring-blue-600" />
                  </label>
                </div>
                <button
                  disabled={!!busy || !effectiveClient}
                  onClick={() =>
                    act("quote", async () => {
                      const q = await api<{ quote_id: string }>("/quotes", { method: "POST", json: { session_id: s.session_id, client_id: effectiveClient, valid_until: validUntil } });
                      router.push(`/quotes/${q.quote_id}`);
                    })
                  }
                  className="mt-4 inline-flex w-full items-center justify-center gap-2 rounded-md bg-violet-700 px-4 py-2.5 font-semibold text-white hover:bg-violet-800 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-600 disabled:bg-slate-300"
                >
                  {busy === "quote" && <Loader2 size={16} className="animate-spin" />} Lưu báo giá
                </button>
              </div>
            ) : (
              <div className="rounded-lg border border-violet-300 bg-white p-4 shadow-sm">
                <h2 className="font-semibold">Báo giá {s.quote.quote_id}</h2>
                <p className="mt-1 text-sm">
                  Trạng thái: <StatePill status={s.quote.status} />
                </p>
                <Link href={`/quotes/${s.quote.quote_id}`} className="mt-3 inline-block rounded-md border border-violet-400 px-3 py-1.5 text-sm font-semibold text-violet-900 hover:bg-violet-50">
                  Mở báo giá →
                </Link>
              </div>
            )}
          </div>
        )
      )}
    </div>
  );
}

function Stepper({ analyzed, locked, blockers }: { analyzed: boolean; locked: boolean; blockers: number }) {
  const steps = [
    { label: "Nhận list", done: true },
    { label: "Đọc & sửa", done: analyzed },
    { label: blockers ? `Rà soát (${blockers})` : "Rà soát", done: analyzed && blockers === 0 },
    { label: "Confirm", done: locked },
  ];
  return (
    <ol className="flex items-center gap-1 text-xs">
      {steps.map((st, i) => (
        <li key={st.label} className="flex items-center gap-1">
          <span className={clsx("rounded-full px-2 py-0.5 font-semibold", st.done ? "bg-emerald-100 text-emerald-900" : "bg-slate-200 text-slate-600")}>
            {i + 1}. {st.label}
          </span>
          {i < steps.length - 1 && <span className="text-slate-300">—</span>}
        </li>
      ))}
    </ol>
  );
}

function ConfirmResult({ s }: { s: SessionView }) {
  const c = s.confirmation;
  const ok = c.order_status === "POS_ACCEPTED";
  return (
    <div className={clsx("rounded-lg border p-4 shadow-sm", ok ? "border-emerald-400 bg-emerald-50" : "border-amber-500 bg-amber-50")}>
      <div className="flex items-center gap-2 text-lg font-bold">
        <Lock size={18} /> {ok ? "Đã gửi POS thành công" : "POS không phản hồi — đã xuất CSV, cần nhập tay"}
      </div>
      <dl className="mt-2 grid gap-x-6 gap-y-1 text-sm sm:grid-cols-2">
        <div>
          Trạng thái đơn: <StatePill status={c.order_status || s.status} /> {!ok && <StatePill status="SENT_OR_EXPORTED" />}
        </div>
        <div>
          Mã tham chiếu (chống nhập trùng): <b className="font-mono">{c.fulfillment_reference}</b>
        </div>
        {c.pos_order_ref && (
          <div>
            POS order ref: <b className="font-mono">{c.pos_order_ref}</b>
          </div>
        )}
        <div>
          Client: <b>{s.client_id}</b>
        </div>
        {c.processing_time_seconds != null && (
          <div>
            Thời gian từ upload → Confirm: <b className="tabular">{c.processing_time_seconds} s</b>
          </div>
        )}
      </dl>
      {c.csv_download_url && (
        <a href={fileUrl(c.csv_download_url)} className="mt-3 inline-flex items-center gap-2 rounded-md bg-amber-700 px-4 py-2 text-sm font-semibold text-white hover:bg-amber-800">
          <Download size={16} /> Tải CSV để nhập POS
        </a>
      )}
      <p className="mt-2 text-xs text-slate-600">Đơn đã khoá, chỉ đọc. POS/ERP là hệ thống mô phỏng (simulated).</p>
    </div>
  );
}
