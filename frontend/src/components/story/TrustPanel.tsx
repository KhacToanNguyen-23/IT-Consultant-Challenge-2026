"use client";

import { ShieldCheck } from "lucide-react";
import { useI18n, type Key } from "@/client/i18n";
import type { SessionView } from "@/client/api";

// Each guardrail points at the SRS requirement that implements and tests it, so a reviewer can trace it.
const GUARDRAILS: { text: Key; ref: string }[] = [
  { text: "trust_g1", ref: "FR-008 · FR-009" },
  { text: "trust_g2", ref: "FR-010" },
  { text: "trust_g3", ref: "FR-016 · FR-039" },
  { text: "trust_g4", ref: "FR-002" },
  { text: "trust_g5", ref: "FR-003 · FR-019" },
  { text: "trust_g6", ref: "FR-029" },
];

/** "Why you can trust this": the guardrails in plain words, plus what the AI did versus what the human decided on THIS order. */
export default function TrustPanel({ session }: { session: SessionView }) {
  const { t } = useI18n();
  const suggested = session.lines.filter((l) => l.match.sku).length;
  const edited = session.lines.filter((l) => l.associate_edited).length;
  const accepted = session.lines.filter((l) => l.line_status === "CUSTOMER_ACCEPTED").length;

  return (
    <details className="story-trust" data-testid="trust-panel">
      <summary>
        <ShieldCheck size={16} aria-hidden />
        <span>{t("trust_title")}</span>
        <span className="story-trust-counts" data-testid="trust-counts">
          {t("trust_counts", { a: suggested, e: edited, s: accepted })}
        </span>
      </summary>
      <ul>
        {GUARDRAILS.map((g) => (
          <li key={g.text}>
            <span>{t(g.text)}</span>
            <code>{g.ref}</code>
          </li>
        ))}
      </ul>
      <p className="story-sim">{t("story_sim_badge")}</p>
    </details>
  );
}
