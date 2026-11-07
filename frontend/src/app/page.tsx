"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { forwardRef, Suspense, useEffect, useRef, useState } from "react";
import { ClipboardList, Eraser, FileUp, Mail, ScanLine, ShieldCheck, X } from "lucide-react";
import { api, ApiError } from "@/client/api";
import { useI18n } from "@/client/i18n";
import { Notice, PosKey, SoftKeys, Terminal, Vfd } from "@/components/pos/Terminal";
import { EMAIL_SAMPLE, SAMPLE_ORDERS } from "@/components/story/samples";
import { Textarea } from "@/components/ui/input";

type Mode = "counter" | "email";

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
  const modeButtons = useRef<HTMLButtonElement[]>([]);
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

  const onModeKeyDown = (e: React.KeyboardEvent<HTMLButtonElement>, index: number) => {
    if (!["ArrowRight", "ArrowDown", "ArrowLeft", "ArrowUp"].includes(e.key)) return;
    e.preventDefault();
    const next = (index + (e.key === "ArrowRight" || e.key === "ArrowDown" ? 1 : -1) + 2) % 2;
    setMode(next === 0 ? "counter" : "email");
    modeButtons.current[next]?.focus();
  };

  return (
    <Terminal
      ticket={
        <div id="intake-panel" role="tabpanel" aria-labelledby={isEmail ? "email-mode-tab" : "counter-mode-tab"} className="paper flex min-h-full flex-col">
          <div className="paper-head">
            <h1 className="paper-title">{t("intake_title")}</h1>
          </div>
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
          <div className="flex flex-wrap items-center justify-between gap-2 px-[18px] pt-3">
            {file ? (
              <span className="text-base font-semibold">{t("selected_file")}</span>
            ) : (
              <div className="min-w-0">
                <label htmlFor="intake" className="block text-base font-semibold">
                  {isEmail ? t("paste_email") : t("paste_list")}
                </label>

              </div>
            )}
            {!isEmail && (
              <PosKey hotkey="F6" size="sm" tone="nav" icon={<FileUp size={16} />} onClick={() => fileRef.current?.click()} className="intake-upload-button !min-h-10">
                {t("key_file")}
              </PosKey>
            )}
          </div>
          {!file && !text.trim() && (
            <div className="story-samples px-[18px] pt-3" data-testid="sample-orders">
              <span className="font-semibold">{t("story_samples_title")}</span>
              <div className="story-sample-grid">
                {(isEmail ? [EMAIL_SAMPLE] : SAMPLE_ORDERS).map((o) => (
                  <button key={o.id} type="button" className="story-sample" data-testid={`sample-${o.id}`} onClick={() => setText(o.text)}>
                    <span className="story-sample-title">{t(o.title)}</span>
                    <span className="story-sample-detail">{t(o.detail)}</span>
                  </button>
                ))}
              </div>
            </div>
          )}
          {file ? (
            <div className="m-[18px] flex items-center gap-3 rounded-lg border border-blue-200 bg-blue-50 p-4" role="status">
              <FileUp size={20} className="flex-none text-blue-800" aria-hidden />
              <span className="min-w-0 flex-1 break-all font-medium">{file.name}</span>
              <button type="button" className="key key--sm flex-none" onClick={() => { setFile(null); if (fileRef.current) fileRef.current.value = ""; }}>
                <X size={15} aria-hidden /> {t("key_remove")}
              </button>
            </div>
          ) : (
            <Textarea
              id="intake"
              value={text}
              onChange={(e) => setText(e.target.value)}
              rows={14}
              placeholder={t(isEmail ? "intake_placeholder_email" : "intake_placeholder_list")}
              className="min-h-0 flex-1 resize-none rounded-none border-0 bg-transparent px-[18px] py-3 font-mono text-[15px] leading-7 shadow-none hover:border-transparent focus:border-transparent focus:ring-0"
            />
          )}
        </div>
      }
      rail={
        <>
          <Vfd top={file ? t("vfd_file") : lineCount ? t("vfd_reading") : t("vfd_ready")} main={file ? "1" : lineCount} sub={file?.name} />
          <div className="pos-screen space-y-3">
            <div className="intake-proof">
              <div className="intake-proof-main"><ShieldCheck size={16} aria-hidden /> {t("masking_proof")}</div>
              <details>
                <summary>{t("masking_limit_title")}</summary>
                <p>{t("intake_hint_pii")}</p>
              </details>
            </div>
            <div role="tablist" aria-label={t("flow_label")} className="grid gap-2">
              <FlowTile id="counter-mode-tab" ref={(el) => { if (el) modeButtons.current[0] = el; }} active={!isEmail} onClick={() => setMode("counter")} onKeyDown={(e) => onModeKeyDown(e, 0)} icon={<ClipboardList size={20} />} title={t("mode_counter")} description={t("mode_counter_sub")} />
              <FlowTile id="email-mode-tab" ref={(el) => { if (el) modeButtons.current[1] = el; }} active={isEmail} onClick={() => setMode("email")} onKeyDown={(e) => onModeKeyDown(e, 1)} icon={<Mail size={20} />} title={t("mode_email")} description={t("mode_email_sub")} />
            </div>
            {error && (
              <Notice tone="bad" alert>
                {error}
              </Notice>
            )}
          </div>
        </>
      }
      keys={
        <SoftKeys
          slots={[
            <PosKey key="clear" hotkey="F3" tone="void" icon={<Eraser size={17} />} onClick={clear} disabled={!text && !file}>
              {t("key_clear")}
            </PosKey>,
            <PosKey key="read" hotkey="F9" tone="go" icon={<ScanLine size={18} />} onClick={submit} busy={busy} disabled={busy}>
              {t("read_list")}
            </PosKey>,
          ]}
        />
      }
    />
  );
}

const FlowTile = forwardRef<HTMLButtonElement, {
  id: string;
  active: boolean;
  onClick: () => void;
  onKeyDown: (event: React.KeyboardEvent<HTMLButtonElement>) => void;
  icon: React.ReactNode;
  title: string;
  description: string;
}>(function FlowTile({ id, active, onClick, onKeyDown, icon, title, description }, ref) {
  return (
    <button id={id} ref={ref} type="button" role="tab" aria-controls="intake-panel" aria-selected={active} tabIndex={active ? 0 : -1} onClick={onClick} onKeyDown={onKeyDown} className="flow-tile tile flex items-start gap-3">
      <span className="flow-tile-icon mt-0.5 flex-none">{icon}</span>
      <span className="min-w-0">
        <span className="block font-[family-name:var(--font-key)] text-base font-semibold leading-tight">{title}</span>
        <span className="flow-tile-description mt-1 block text-xs leading-5">{description}</span>
      </span>
    </button>
  );
});
