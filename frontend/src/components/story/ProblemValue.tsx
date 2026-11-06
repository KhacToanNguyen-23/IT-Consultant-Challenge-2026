"use client";

import { PackageCheck } from "lucide-react";
import { useI18n, type Key } from "@/client/i18n";
import { SAMPLE_ORDERS } from "./samples";

const FLOW: Key[] = ["story_how_read", "story_how_match", "story_how_substitute", "story_how_confirm"];

/** POS-sized Round 1 value strip. The active work stays in the intake form. */
export default function ProblemValue({ compact, onSample }: { compact: boolean; onSample: (text: string) => void }) {
  const { t } = useI18n();

  return (
    <section className="round1-posband" aria-label="Round 1" data-testid="problem-value">
      <div className="round1-posband-main">
        <span className="round1-posband-tag">{t("story_eyebrow")}</span>
        <strong className="round1-posband-lines">{t("story_compact")}</strong>
        <span className="round1-posband-target">{t("story_title_note")}</span>
        {!compact && (
          <button type="button" className="story-quick-sample" data-testid="quick-happy-path" onClick={() => onSample(SAMPLE_ORDERS[0].text)}>
            <PackageCheck size={15} aria-hidden /> {t("story_quick_sample")}
          </button>
        )}
      </div>
      <ol className="round1-posband-flow" aria-label="Flow 1">
        {FLOW.map((key, index) => (
          <li key={key}>
            <span>{t(key)}</span>
            {index < FLOW.length - 1 && <span className="round1-posband-arrow" aria-hidden="true">&gt;</span>}
          </li>
        ))}
      </ol>
      <small className="round1-posband-footnote">*Team estimate; simulated target, not measured.</small>
    </section>
  );
}