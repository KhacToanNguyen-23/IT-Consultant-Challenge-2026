"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import clsx from "clsx";
import { api, type Health } from "@/client/api";
import { useI18n, type Lang } from "@/client/i18n";
import { PosKey } from "@/components/pos/Terminal";

export default function AppHeader() {
  const path = usePathname();
  const { t, lang, setLang } = useI18n();
  const [health, setHealth] = useState<Health | null>(null);
  const [busy, setBusy] = useState(false);

  const load = useCallback(() => {
    api<Health>("/health").then(setHealth).catch(() => setHealth(null));
  }, []);

  useEffect(() => {
    load();
    const timer = setInterval(load, 10000);
    const onChange = () => load();
    window.addEventListener("sitedesk:health", onChange);
    return () => {
      clearInterval(timer);
      window.removeEventListener("sitedesk:health", onChange);
    };
  }, [load]);

  const toggle = async (kind: "ai" | "pos") => {
    if (!health) return;
    setBusy(true);
    try {
      await api("/admin/fail-modes", { method: "POST", json: { [kind]: kind === "ai" ? !health.ai_fail_mode : !health.pos_fail_mode } });
      load();
      window.dispatchEvent(new Event("sitedesk:health"));
    } finally {
      setBusy(false);
    }
  };

  const onCounter = path === "/" || path.startsWith("/sessions");

  return (
    <header className="pos-status print:hidden">
      <Link href="/" className="pos-brand">
        SiteDesk
      </Link>
      <nav className="flex gap-2" aria-label={t("flow_label")}>
        <PosKey size="sm" hotkey="F1" href="/" tone={onCounter ? "on" : "std"} current={onCounter} className="w-28">
          {t("nav_counter")}
        </PosKey>
        <PosKey size="sm" hotkey="F2" href="/quotes" tone={onCounter ? "std" : "on"} current={!onCounter} className="w-28">
          {t("nav_quotes")}
        </PosKey>
      </nav>

      <div className="ml-auto flex flex-wrap items-center gap-2">
        <span className="text-[var(--case-ink-soft)]" title={t("mock_login_title")}>
          EMP-1042, {t("store_terminal")} DK-CPH-04, <i>{t("mock_login")}</i>
        </span>
        <FailToggle label={t("ai_fail")} title={t("demo_toggle")} on={!!health?.ai_fail_mode} disabled={busy || !health} onClick={() => toggle("ai")} />
        <FailToggle label={t("pos_fail")} title={t("demo_toggle")} on={!!health?.pos_fail_mode} disabled={busy || !health} onClick={() => toggle("pos")} />
        <span className="inline-flex items-center gap-1.5 font-semibold">
          <span className={clsx("lamp", !health ? "lamp--bad" : health.status === "healthy" ? "lamp--ok" : "lamp--warn")} aria-hidden />
          {!health ? t("api_offline") : health.status === "healthy" ? t("system_ok") : t("degraded")}
        </span>
        <Clock />
        <div role="group" aria-label={t("lang_switch")} className="flex gap-1">
          {(["en", "vi"] as Lang[]).map((l) => (
            <button key={l} type="button" aria-pressed={lang === l} onClick={() => setLang(l)} className={clsx("pos-switch uppercase", lang === l && "!bg-[var(--vfd)] !text-[var(--vfd-bg)]")}>
              {l}
            </button>
          ))}
        </div>
      </div>
    </header>
  );
}

/** Renders after mount only: server and browser clocks would otherwise fail hydration. */
function Clock() {
  const [now, setNow] = useState<string | null>(null);
  useEffect(() => {
    const tick = () => setNow(new Date().toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit" }));
    tick();
    const timer = setInterval(tick, 10000);
    return () => clearInterval(timer);
  }, []);
  return <span className="pos-clock tabular">{now ?? "--:--"}</span>;
}

function FailToggle({ label, title, on, disabled, onClick }: { label: string; title: string; on: boolean; disabled: boolean; onClick: () => void }) {
  return (
    <button type="button" role="switch" aria-checked={on} disabled={disabled} onClick={onClick} title={title} className="pos-switch">
      <span className={clsx("lamp", on && "lamp--bad")} aria-hidden />
      {label}: {on ? "ON" : "off"}
    </button>
  );
}
