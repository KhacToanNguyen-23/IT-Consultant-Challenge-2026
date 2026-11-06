"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import clsx from "clsx";
import { ChevronDown, ClipboardList, FileText, FlaskConical, UserRound, WandSparkles } from "lucide-react";
import { api, type Health } from "@/client/api";
import { useI18n } from "@/client/i18n";
import { PosKey } from "@/components/pos/Terminal";

export default function AppHeader() {
  const path = usePathname();
  const { t } = useI18n();
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

  const onCounter = path === "/" || path.startsWith("/sessions/");
  const onQuotes = path === "/quotes" || path.startsWith("/quotes/");
  const onDictionary = path === "/store-dictionary";

  return (
    <>
      <aside className="pos-sidebar print:hidden">
        <Link href="/" className="sidebar-brand" aria-label="SiteDesk home">
          <span className="sidebar-mark">SD</span>
          <span className="sidebar-brand-name">SiteDesk</span>
        </Link>
        <nav className="sidebar-nav" aria-label={t("flow_label")}>
          <PosKey size="sm" hotkey="F1" href="/" tone={onCounter ? "on" : "std"} current={onCounter} ariaLabel={t("nav_counter")} icon={<ClipboardList size={18} />} className="side-nav-link">
            <span className="sidebar-link-text">{t("nav_counter")}</span>
          </PosKey>
          <PosKey size="sm" hotkey="F2" href="/quotes" tone={onQuotes ? "on" : "std"} current={onQuotes} ariaLabel={t("nav_quotes")} icon={<FileText size={18} />} className="side-nav-link">
            <span className="sidebar-link-text">{t("nav_quotes")}</span>
          </PosKey>
          <PosKey size="sm" href="/store-dictionary" tone={onDictionary ? "on" : "std"} current={onDictionary} ariaLabel={t("nav_dictionary")} icon={<WandSparkles size={18} />} className="side-nav-link">
            <span className="sidebar-link-text">{t("nav_dictionary")}</span>
          </PosKey>
        </nav>

        <div className="sidebar-spacer" />
        <div className="sidebar-footer">
          <details className="demo-menu sidebar-demo">
            <summary className="sidebar-tool cursor-pointer list-none" aria-label={t("demo_menu")}>
              <FlaskConical size={17} aria-hidden /> <span className="sidebar-link-text">{t("demo_menu")}</span> <ChevronDown className="sidebar-chevron" size={14} aria-hidden />
            </summary>
            <div className="demo-menu-panel">
              <FailToggle label={t("ai_fail")} title={t("demo_toggle")} on={!!health?.ai_fail_mode} disabled={busy || !health} onClick={() => toggle("ai")} />
              <FailToggle label={t("pos_fail")} title={t("demo_toggle")} on={!!health?.pos_fail_mode} disabled={busy || !health} onClick={() => toggle("pos")} />
            </div>
          </details>
          <Link href="/login" className="sidebar-operator" title={t("mock_login_title")} aria-label={`${t("mock_login_title")}: EMP-1042`}>
            <UserRound size={17} aria-hidden /> <span className="sidebar-link-text">EMP-1042</span>
          </Link>
        </div>
      </aside>

      <header className="pos-topbar print:hidden">
        <div className="topbar-location"><span className="topbar-location-dot" /> {t("store_terminal")} <span className="topbar-divider">/</span> DK-CPH-04</div>
        <div className="topbar-status">
          <span className="inline-flex items-center gap-2 font-semibold">
            <span className={clsx("lamp", !health ? "lamp--bad" : health.status === "healthy" ? "lamp--ok" : "lamp--warn")} aria-hidden />
            <span>{!health ? t("api_offline") : health.status === "healthy" ? t("system_ok") : t("degraded")}</span>
          </span>
          <Clock />
        </div>
      </header>
    </>
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
