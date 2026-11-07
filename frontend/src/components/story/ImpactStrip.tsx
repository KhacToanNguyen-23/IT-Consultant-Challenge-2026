"use client";

import { useEffect, useState } from "react";
import { useI18n } from "@/client/i18n";
import type { Line, SessionView } from "@/client/api";



const mmss = (s: number) => `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;

/** Lines whose sold quantity differs from what the customer typed: the unit conversions the system did for the associate. */
export const convertedLines = (lines: Line[]) =>
  lines.filter((l) => l.conversion.selling_quantity != null && l.parsed.quantity != null && l.conversion.selling_quantity !== l.parsed.quantity).length;

/** High-confidence lines the associate did not have to touch (the Round 1 "zero-touch" idea, for THIS order only). */
export const zeroTouchLines = (lines: Line[]) => lines.filter((l) => l.match.band === "HIGH" && !l.associate_edited).length;

/**
 * Real, measured numbers for the order on screen. Nothing here is estimated:
 * analysis time comes from the API, the timer runs in this browser from the moment the screen opened.
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

  const analysed = Number(session.stage_timings_ms.total_ms);
  const cells: { value: string; label: string; testid: string }[] = [
    { value: Number.isFinite(analysed) && analysed > 0 ? `${Math.round(analysed)} ms` : "—", label: t("impact_analysed"), testid: "impact-analysed" },
    { value: `${zeroTouchLines(session.lines)}/${session.lines.length}`, label: t("impact_zero"), testid: "impact-zero" },
    { value: mmss(seconds), label: `${t("impact_time")} · ${t("impact_target")}`, testid: "impact-time" },
  ];

  return (
    <div className="story-impact" data-testid="impact-strip" aria-label={t("impact_title")}>
      {cells.map((c) => (
        <div key={c.testid} data-testid={c.testid}>
          <strong className="tabular">{c.value}</strong>
          <span>{c.label}</span>
        </div>
      ))}
    </div>
  );
}
