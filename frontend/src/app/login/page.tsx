"use client";

import { useRouter } from "next/navigation";
import { BadgeCheck, LogIn, ShieldCheck } from "lucide-react";
import { useI18n } from "@/client/i18n";
import { Notice, PosKey, SoftKeys, Terminal, Vfd } from "@/components/pos/Terminal";

/** SRS MVP-FR-032: a clearly labelled demo sign-in; no credentials or real SSO. */
export default function LoginPage() {
  const router = useRouter();
  const { t } = useI18n();

  return (
    <Terminal
      ticket={
        <div className="paper flex min-h-full flex-col">
          <div className="paper-head">
            <div className="text-sm soft">SiteDesk · {t("login_mock_sso")}</div>
            <h1 className="paper-title">{t("login_title")}</h1>
            <p className="mt-1 text-sm soft">{t("login_sub")}</p>
          </div>
          <div className="grid flex-1 place-items-center px-5 py-8">
            <div className="w-full max-w-xl space-y-4">
              <div className="flex items-center gap-4 rounded-md border border-[var(--rule)] bg-white p-5">
                <div className="grid h-14 w-14 flex-none place-items-center rounded-full bg-[#e6e9e5] text-[var(--ink)]" aria-hidden>
                  <BadgeCheck size={28} />
                </div>
                <div className="min-w-0">
                  <div className="text-xs font-semibold uppercase tracking-wide soft">{t("login_operator")}</div>
                  <div className="font-[family-name:var(--font-key)] text-2xl font-bold">EMP-1042</div>
                  <div className="text-sm soft">DK-CPH-04 · Copenhagen counter</div>
                </div>
              </div>
              <Notice tone="warn" icon={<ShieldCheck size={17} />}>
                {t("login_idle")}
              </Notice>
            </div>
          </div>
        </div>
      }
      rail={
        <>
          <Vfd top={t("login_mock_sso")} main="DEMO" />
          <div className="pos-screen flex flex-col justify-between gap-4">
            <div className="space-y-3">
              <h2 className="screen-title">{t("login_operator")}</h2>
              <div className="tile flex items-center gap-3 !bg-[#f7faf8]">
                <span className="grid h-10 w-10 flex-none place-items-center rounded-full bg-[#dcf3e5] text-emerald-900" aria-hidden>
                  <BadgeCheck size={21} />
                </span>
                <span>
                  <span className="block font-semibold">EMP-1042</span>
                  <span className="block text-xs soft">DK-CPH-04</span>
                </span>
              </div>
              <p className="screen-note">{t("login_mock_sso")}</p>
            </div>
            <PosKey tone="go" hotkey="F9" icon={<LogIn size={18} />} onClick={() => router.push("/")}>
              {t("login_continue")}
            </PosKey>
          </div>
        </>
      }
      keys={
        <SoftKeys
          slots={[
            <PosKey key="home" hotkey="F3" href="/">
              {t("nav_counter")}
            </PosKey>,
            null,
            null,
            null,
            null,
            <PosKey key="continue" hotkey="F9" tone="go" icon={<LogIn size={18} />} onClick={() => router.push("/")}>
              {t("login_continue")}
            </PosKey>,
          ]}
        />
      }
    />
  );
}
