"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import clsx from "clsx";
import { api, type Health } from "@/client/api";
import { useI18n, type Lang } from "@/client/i18n";

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

  const nav = [
    { href: "/", label: t("nav_counter"), active: path === "/" || path.startsWith("/sessions") },
    { href: "/quotes", label: t("nav_quotes"), active: path.startsWith("/quotes") },
  ];

  return (
    <header className="border-b border-slate-200 bg-white print:hidden">
      <div className="mx-auto flex max-w-[1400px] flex-wrap items-center gap-x-6 gap-y-2 px-4 py-3">
        <Link href="/" className="flex items-center gap-2 font-bold text-slate-900">
          <span className="grid h-7 w-7 place-items-center rounded-md bg-slate-900 text-xs text-white">SD</span>
          SiteDesk
        </Link>
        <nav className="flex gap-1">
          {nav.map((n) => (
            <Link
              key={n.href}
              href={n.href}
              className={clsx(
                "rounded-md px-3 py-1.5 text-sm font-medium focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-600",
                n.active ? "bg-slate-900 text-white" : "text-slate-700 hover:bg-slate-100"
              )}
            >
              {n.label}
            </Link>
          ))}
        </nav>
        <div className="ml-auto flex flex-wrap items-center gap-2 text-xs">
          <span className="rounded border border-slate-200 bg-slate-50 px-2 py-1 text-slate-600" title={t("mock_login_title")}>
            EMP-1042 · DK-CPH-04 · <i>{t("mock_login")}</i>
          </span>
          <FailToggle label={t("ai_fail")} title={t("demo_toggle")} on={!!health?.ai_fail_mode} disabled={busy || !health} onClick={() => toggle("ai")} />
          <FailToggle label={t("pos_fail")} title={t("demo_toggle")} on={!!health?.pos_fail_mode} disabled={busy || !health} onClick={() => toggle("pos")} />
          <span
            className={clsx(
              "rounded px-2 py-1 font-semibold",
              !health ? "bg-red-100 text-red-900" : health.status === "healthy" ? "bg-emerald-100 text-emerald-900" : "bg-amber-100 text-amber-900"
            )}
          >
            {!health ? t("api_offline") : health.status === "healthy" ? t("system_ok") : t("degraded")}
          </span>
          <div role="group" aria-label={t("lang_switch")} className="flex overflow-hidden rounded border border-slate-300">
            {(["en", "vi"] as Lang[]).map((l) => (
              <button
                key={l}
                type="button"
                aria-pressed={lang === l}
                onClick={() => setLang(l)}
                className={clsx(
                  "px-2 py-1 font-semibold uppercase focus:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-blue-600",
                  lang === l ? "bg-slate-900 text-white" : "bg-white text-slate-600 hover:bg-slate-50"
                )}
              >
                {l}
              </button>
            ))}
          </div>
        </div>
      </div>
    </header>
  );
}

function FailToggle({ label, title, on, disabled, onClick }: { label: string; title: string; on: boolean; disabled: boolean; onClick: () => void }) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={on}
      disabled={disabled}
      onClick={onClick}
      title={title}
      className={clsx(
        "rounded border px-2 py-1 font-semibold focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-600 disabled:opacity-50",
        on ? "border-red-500 bg-red-50 text-red-900" : "border-slate-300 bg-white text-slate-600 hover:bg-slate-50"
      )}
    >
      {label}: {on ? "ON" : "off"}
    </button>
  );
}
