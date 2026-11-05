"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useRef, useState } from "react";
import { ClipboardList, Eraser, FileUp, Mail, ScanLine, Sparkles } from "lucide-react";
import { api, ApiError } from "@/client/api";
import { useI18n } from "@/client/i18n";
import { Notice, PosKey, SoftKeys, Terminal, Vfd } from "@/components/pos/Terminal";

type Mode = "counter" | "email";

// Customer content stays in the customer's language (Danish) in both UI languages
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

// useSearchParams needs a Suspense boundary for the production build
export default function IntakeRoute() {
  return (
    <Suspense>
      <IntakePage />
    </Suspense>
  );
}

function IntakePage() {
  const router = useRouter();
  const emailLink = useSearchParams().get("mode") === "email";
  const { t } = useI18n();
  const [mode, setMode] = useState<Mode>("counter");
  const [text, setText] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  // The quote list links here with ?mode=email; F1 returns to the plain counter URL
  useEffect(() => setMode(emailLink ? "email" : "counter"), [emailLink]);

  const clear = () => {
    setText("");
    setFile(null);
    setError(null);
    if (fileRef.current) fileRef.current.value = "";
  };

  const submit = async () => {
    setError(null);
    if (!file && !text.trim()) {
      setError(t("need_input"));
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

  const lineCount = text.split("\n").filter((l) => l.trim()).length;
  const isEmail = mode === "email";

  return (
    <Terminal
      ticket={
        <div className="paper flex min-h-full flex-col">
          <div className="paper-head">
            <h1 className="paper-title">{t("intake_title")}</h1>
            <p className="mt-1 text-sm soft">{t("intake_sub")}</p>
          </div>
          <label htmlFor="intake" className="px-[18px] pt-3 text-base font-semibold">
            {isEmail ? t("paste_email") : t("paste_list")}
          </label>
          <textarea
            id="intake"
            value={text}
            onChange={(e) => {
              setText(e.target.value);
              if (e.target.value) setFile(null);
            }}
            rows={14}
            placeholder={isEmail ? "Fra: ...\nHej, ...\nTimber 45x95 C24 - 120 m\n..." : "Timber 45x95 C24 - 120 m\nRockwool FlexiBatts 95mm - 15 pk\n..."}
            className="font-mono mt-1 w-full flex-1 resize-none bg-transparent px-[18px] py-2 text-[15px] leading-7 placeholder:text-slate-400"
          />
        </div>
      }
      rail={
        <>
          <Vfd top={file ? t("vfd_file") : lineCount ? t("vfd_reading") : t("vfd_ready")} main={file ? "1" : lineCount} sub={file?.name} />
          <div className="pos-screen space-y-3">
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
            <div role="tablist" aria-label={t("flow_label")} className="grid gap-2">
              <FlowTile active={!isEmail} onClick={() => setMode("counter")} icon={<ClipboardList size={20} />} title={t("mode_counter")} sub={t("mode_counter_sub")} />
              <FlowTile active={isEmail} onClick={() => setMode("email")} icon={<Mail size={20} />} title={t("mode_email")} sub={t("mode_email_sub")} />
            </div>
            {error && (
              <Notice tone="bad" alert>
                {error}
              </Notice>
            )}
            <ul className="screen-note list-disc space-y-1.5 pl-4">
              <li>{t("intake_hint_pdf")}</li>
              <li>{t("intake_hint_pii")}</li>
            </ul>
          </div>
        </>
      }
      keys={
        <SoftKeys
          slots={[
            <PosKey key="clear" hotkey="F3" tone="void" icon={<Eraser size={17} />} onClick={clear} disabled={!text && !file}>
              {t("key_clear")}
            </PosKey>,
            <PosKey
              key="sample"
              hotkey="F4"
              icon={<Sparkles size={17} />}
              onClick={() => {
                setFile(null);
                setText(isEmail ? SAMPLE_EMAIL : SAMPLE_COUNTER);
              }}
            >
              {t("key_sample")}
            </PosKey>,
            <PosKey key="file" hotkey="F6" icon={<FileUp size={17} />} onClick={() => fileRef.current?.click()} disabled={isEmail}>
              {t("key_file")}
            </PosKey>,
            null,
            null,
            <PosKey key="read" hotkey="F9" tone="go" icon={<ScanLine size={18} />} onClick={submit} busy={busy} disabled={busy}>
              {t("read_list")}
            </PosKey>,
          ]}
        />
      }
    />
  );
}

function FlowTile({ active, onClick, icon, title, sub }: { active: boolean; onClick: () => void; icon: React.ReactNode; title: string; sub: string }) {
  return (
    <button type="button" role="tab" aria-selected={active} aria-pressed={active} onClick={onClick} className="tile flex items-start gap-3">
      <span className="mt-0.5 flex-none">{icon}</span>
      <span>
        <span className="block font-[family-name:var(--font-key)] text-xl font-bold leading-tight">{title}</span>
        <span className="block text-sm soft">{sub}</span>
      </span>
    </button>
  );
}
