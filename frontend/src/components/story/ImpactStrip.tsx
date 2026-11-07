"use client";

import { useEffect, useState } from "react";
import { Timer } from "lucide-react";
import { useI18n } from "@/client/i18n";
import type { SessionView } from "@/client/api";



const mmss = (s: number) => `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;

/**
 * Tracks the associate's active review time for the order. The clock stops once the order is confirmed.
 */
export default function ImpactStrip({ session }: { session: SessionView }) {
  const { t } = useI18n();
  const [seconds, setSeconds] = useState(0);
  useEffect(() => {
    if (session.locked) return; // the clock stops when the order is confirmed
    const started = Date.now();
    const id = window.setInterval(() => setSeconds(Math.floor((Date.now() - started) / 1000)), 1000);
    return () => window.clearInterval(id);
  }, [session.locked, session.session_id]);
  const elapsed = session.locked && session.confirmation.processing_time_seconds != null
    ? session.confirmation.processing_time_seconds
    : seconds;
  const formatted = mmss(elapsed);

  return (
    <div className="story-impact" data-testid="impact-strip">
      <div className="impact-timer-chip" data-testid="impact-time" role="timer" aria-live="off" aria-label={`${t("impact_time")}: ${formatted}. ${t("impact_target")}`} title={`${t("impact_time")}: ${formatted} · ${t("impact_target")}`}>
        <Timer size={14} aria-hidden="true" />
        <strong className="tabular">{formatted}</strong>
      </div>
    </div>
  );
}
