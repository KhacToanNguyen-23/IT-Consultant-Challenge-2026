"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import clsx from "clsx";
import { Loader2 } from "lucide-react";
import { useI18n } from "@/client/i18n";

export type KeyTone = "std" | "go" | "void" | "hold" | "nav" | "quote" | "on";

const isEditing = (el: EventTarget | null) => el instanceof HTMLElement && (el.isContentEditable || ["INPUT", "TEXTAREA", "SELECT"].includes(el.tagName));

/** Binds a physical key. Function keys work while typing; other keys wait until focus leaves the field. */
export function useHotkey(key: string | undefined, fire: () => void, enabled = true) {
  const latest = useRef({ fire, enabled });
  latest.current = { fire, enabled };

  useEffect(() => {
    if (!key) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key !== key || e.ctrlKey || e.altKey || e.metaKey || e.shiftKey) return;
      if (!/^F\d+$/.test(key) && isEditing(e.target)) return;
      e.preventDefault();
      if (!e.repeat && latest.current.enabled) latest.current.fire();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [key]);
}

interface PosKeyProps {
  tone?: KeyTone;
  size?: "md" | "sm" | "digit";
  hotkey?: string;
  icon?: React.ReactNode;
  busy?: boolean;
  disabled?: boolean;
  href?: string;
  /** Opens outside the app (print views, CSV downloads). */
  external?: boolean;
  current?: boolean;
  ariaLabel?: string;
  onClick?: () => void;
  className?: string;
  children: React.ReactNode;
}

/** One keycap. A hotkey presses the real element, so its disabled state and current props always apply. */
export function PosKey({ tone = "std", size = "md", hotkey, icon, busy, disabled, href, external, current, ariaLabel, onClick, className, children }: PosKeyProps) {
  const ref = useRef<HTMLButtonElement & HTMLAnchorElement>(null);
  useHotkey(hotkey, () => ref.current?.click(), !disabled);

  const cls = clsx("key", tone !== "std" && `key--${tone}`, size !== "md" && `key--${size}`, className);
  const body = (
    <>
      {hotkey && <span className="key-fn">{hotkey === "Escape" ? "Esc" : hotkey}</span>}
      <span className="key-label">
        {busy ? <Loader2 size={17} className="animate-spin" aria-hidden /> : icon}
        <span className="min-w-0">{children}</span>
      </span>
    </>
  );

  if (href && !disabled) {
    if (external)
      return (
        <a ref={ref} href={href} target="_blank" rel="noreferrer" className={cls} aria-label={ariaLabel}>
          {body}
        </a>
      );
    return (
      <Link ref={ref} href={href} className={cls} aria-label={ariaLabel} aria-current={current ? "page" : undefined}>
        {body}
      </Link>
    );
  }
  return (
    <button ref={ref} type="button" disabled={disabled} onClick={onClick} className={cls} aria-label={ariaLabel} aria-pressed={current}>
      {body}
    </button>
  );
}

/** The hardware key row: six fixed slots, empty ones stay as blank caps so keys never move. */
export function SoftKeys({ slots }: { slots: React.ReactNode[] }) {
  return (
    <div className="pos-softkeys print:hidden">
      {slots.map((slot, i) => (
        <div key={i} className={clsx("min-w-0 [&>.key]:h-[calc(100%-3px)] [&>.key]:w-full", !slot && "hidden sm:block")}>
          {slot || <div className="key key--blank" aria-hidden />}
        </div>
      ))}
    </div>
  );
}

export function Terminal({ ticket, rail, keys }: { ticket: React.ReactNode; rail: React.ReactNode; keys: React.ReactNode }) {
  return (
    <div className="pos-terminal">
      <section className="pos-ticket">
        <div className="pos-feed">
          {ticket}
          <div className="paper-tear" aria-hidden />
        </div>
      </section>
      <aside className="pos-rail">{rail}</aside>
      {keys}
    </div>
  );
}

export function Vfd({ top, main, unit, sub }: { top: React.ReactNode; main: React.ReactNode; unit?: string; sub?: React.ReactNode }) {
  return (
    <div className="vfd" role="status">
      <div className="vfd-top">{top}</div>
      <div className="vfd-main">
        <span className="min-w-0 truncate">{main}</span>
        {unit && <span className="vfd-unit">{unit}</span>}
      </div>
      <div className="vfd-sub">{sub}</div>
    </div>
  );
}

export function Notice({ tone, icon, children, alert }: { tone: "warn" | "bad" | "good" | "quote"; icon?: React.ReactNode; children: React.ReactNode; alert?: boolean }) {
  return (
    <div role={alert ? "alert" : "status"} className={`notice notice--${tone}`}>
      {icon && <span className="mt-0.5 flex-none">{icon}</span>}
      <div className="min-w-0">{children}</div>
    </div>
  );
}

export function LoadingTerminal({ error }: { error: string | null }) {
  const { t } = useI18n();
  return (
    <div className="pos-loading">
      {error ? (
        <p role="alert" className="max-w-md text-center text-base">
          {error}
        </p>
      ) : (
        <Loader2 className="animate-spin" aria-label={t("loading")} />
      )}
    </div>
  );
}

/** A key that must be pressed twice within a few seconds, for actions that cannot be undone. */
export function useArmed(ms = 3000) {
  const [armed, setArmed] = useState(false);
  useEffect(() => {
    if (!armed) return;
    const timer = setTimeout(() => setArmed(false), ms);
    return () => clearTimeout(timer);
  }, [armed, ms]);
  return { armed, arm: () => setArmed(true), disarm: () => setArmed(false) };
}
