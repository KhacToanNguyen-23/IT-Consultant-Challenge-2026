"use client";

import { useRouter } from "next/navigation";
import { useRef, useState } from "react";
import clsx from "clsx";
import { FileUp, Mail, ClipboardList, Loader2 } from "lucide-react";
import { api, ApiError } from "@/client/api";

type Mode = "counter" | "email";

const SAMPLE_COUNTER = `Timber 45x95 C24 - 120 m
45x95 C18 - 30 stk
Regel 45x95 - 20 stk
Rockwool FlexiBatts 95mm - 15 pk
Gips vådrum 12.5mm - 10 plader
Isolering 95mm 60 m2
Murmørtel 25kg - 5 sække
Terrassebræt 28x120 trykimp 10 x 4.2m`;

const SAMPLE_EMAIL = `Fra: kunde@byg-firma.dk
Emne: Tilbud til projekt Valby

Hej, kan I give et tilbud på følgende til levering næste uge?
Ring gerne på +45 22 33 44 55.

Timber 45x95 C24 - 120 m
Rockwool FlexiBatts 95mm - 15 pk
Gips vådrum 12.5mm - 10 plader
Terrassebræt 28x120 trykimp 10 x 4.2m

Mvh
Jens`;

export default function IntakePage() {
  const router = useRouter();
  const [mode, setMode] = useState<Mode>("counter");
  const [text, setText] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  const submit = async () => {
    setError(null);
    if (!file && !text.trim()) {
      setError("Dán danh sách hoặc chọn file trước.");
      return;
    }
    setBusy(true);
    try {
      const input_type = mode === "email" ? "email" : file ? "file" : "paste_text";
      const s = await api<{ session_id: string }>("/sessions", { method: "POST", json: { input_type, market: "DK" } });
      if (file) {
        const fd = new FormData();
        fd.append("file", file);
        fd.append("language_hint", "DA");
        await api(`/sessions/${s.session_id}/ingest`, { method: "POST", body: fd });
      } else {
        await api(`/sessions/${s.session_id}/ingest`, { method: "POST", json: { text, language_hint: "DA" } });
      }
      router.push(`/sessions/${s.session_id}`);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : String(e));
      setBusy(false);
    }
  };

  return (
    <div className="mx-auto max-w-3xl">
      <h1 className="text-2xl font-bold">Nhận danh sách vật tư</h1>
      <p className="mt-1 text-sm text-slate-600">
        Bước 1/4 · Upload hoặc dán danh sách. Hệ thống che email & số điện thoại trước khi xử lý, sau đó bạn kiểm tra từng dòng.
      </p>

      <div role="tablist" aria-label="Luồng" className="mt-5 grid grid-cols-2 gap-2">
        <ModeTab active={mode === "counter"} onClick={() => setMode("counter")} icon={<ClipboardList size={18} />} title="Tại quầy" sub="Luồng 1 · khách đứng chờ → đơn ngay" />
        <ModeTab active={mode === "email"} onClick={() => setMode("email")} icon={<Mail size={18} />} title="Email báo giá" sub="Luồng 2 · dán email khách → lưu báo giá" />
      </div>

      <div className="mt-4 rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
        <label htmlFor="intake" className="flex items-center justify-between text-sm font-semibold">
          {mode === "email" ? "Dán nội dung email của khách" : "Dán danh sách (mỗi dòng một vật tư)"}
          <button
            type="button"
            className="text-xs font-medium text-blue-700 hover:underline"
            onClick={() => {
              setFile(null);
              setText(mode === "email" ? SAMPLE_EMAIL : SAMPLE_COUNTER);
            }}
          >
            Dùng dữ liệu mẫu
          </button>
        </label>
        <textarea
          id="intake"
          value={text}
          onChange={(e) => {
            setText(e.target.value);
            if (e.target.value) setFile(null);
          }}
          rows={12}
          placeholder={mode === "email" ? "Fra: ...\nHej, ...\nTimber 45x95 C24 - 120 m\n..." : "Timber 45x95 C24 - 120 m\nRockwool FlexiBatts 95mm - 15 pk\n..."}
          className="mt-2 w-full rounded-md border border-slate-300 p-3 font-mono text-sm focus:border-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-600/30"
        />

        {mode === "counter" && (
          <div className="mt-3 flex flex-wrap items-center gap-3 text-sm">
            <span className="text-slate-500">hoặc</span>
            <button
              type="button"
              onClick={() => fileRef.current?.click()}
              className="inline-flex items-center gap-2 rounded-md border border-slate-300 bg-white px-3 py-1.5 font-medium hover:bg-slate-50 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-600"
            >
              <FileUp size={16} /> Chọn file PDF / XLSX / CSV
            </button>
            <input
              ref={fileRef}
              type="file"
              accept=".pdf,.xlsx,.csv,.txt"
              className="hidden"
              onChange={(e) => {
                const f = e.target.files?.[0] || null;
                setFile(f);
                if (f) setText("");
              }}
            />
            {file && <span className="font-medium text-slate-800">{file.name}</span>}
          </div>
        )}

        <ul className="mt-3 list-disc space-y-0.5 pl-5 text-xs text-slate-500">
          <li>PDF phải có text (PDF scan ảnh không được hỗ trợ — hãy dán hoặc gõ lại). Tối đa 5 MB, 1 file.</li>
          <li>Email & số điện thoại được che bằng regex. Tên, địa chỉ trong văn bản tự do <b>chưa được đảm bảo</b> che.</li>
        </ul>

        {error && <p role="alert" className="mt-3 rounded-md border border-red-300 bg-red-50 px-3 py-2 text-sm text-red-900">{error}</p>}

        <div className="mt-4 flex justify-end">
          <button
            type="button"
            onClick={submit}
            disabled={busy}
            className="inline-flex items-center gap-2 rounded-md bg-slate-900 px-5 py-2 text-sm font-semibold text-white hover:bg-slate-800 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-600 focus-visible:ring-offset-2 disabled:opacity-60"
          >
            {busy && <Loader2 size={16} className="animate-spin" />} Đọc danh sách →
          </button>
        </div>
      </div>
    </div>
  );
}

function ModeTab({ active, onClick, icon, title, sub }: { active: boolean; onClick: () => void; icon: React.ReactNode; title: string; sub: string }) {
  return (
    <button
      type="button"
      role="tab"
      aria-selected={active}
      onClick={onClick}
      className={clsx(
        "flex items-start gap-3 rounded-lg border p-3 text-left focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-600",
        active ? "border-slate-900 bg-white shadow-sm ring-1 ring-slate-900" : "border-slate-200 bg-white/60 hover:bg-white"
      )}
    >
      <span className={clsx("mt-0.5", active ? "text-slate-900" : "text-slate-400")}>{icon}</span>
      <span>
        <span className="block text-sm font-semibold">{title}</span>
        <span className="block text-xs text-slate-500">{sub}</span>
      </span>
    </button>
  );
}
