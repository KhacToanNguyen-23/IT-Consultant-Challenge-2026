"use client";

import { useEffect, useState } from "react";
import { AlertTriangle, BadgeCheck, Clock, PackageCheck, ScanLine, ShieldCheck, Sparkles } from "lucide-react";
import { useI18n, type Key } from "@/client/i18n";
import { SAMPLE_ORDERS } from "./samples";

const PAINS: { icon: typeof Clock; pain: Key; note: Key; fix: Key }[] = [
  { icon: Clock, pain: "story_pain_1_pain", note: "story_pain_1_note", fix: "story_pain_1_fix" },
  { icon: PackageCheck, pain: "story_pain_2_pain", note: "story_pain_2_note", fix: "story_pain_2_fix" },
  { icon: AlertTriangle, pain: "story_pain_3_pain", note: "story_pain_3_note", fix: "story_pain_3_fix" },
];

const STEPS: { icon: typeof Sparkles; label: Key; who: "ai" | "you" }[] = [
  { icon: ScanLine, label: "story_how_read", who: "ai" },
  { icon: Sparkles, label: "story_how_match", who: "ai" },
  { icon: PackageCheck, label: "story_how_substitute", who: "ai" },
  { icon: BadgeCheck, label: "story_how_confirm", who: "you" },
];

const TRUST: Key[] = ["story_trust_1", "story_trust_2", "story_trust_3", "story_trust_4"];
const TARGETS: Key[] = ["story_target_1", "story_target_2", "story_target_3", "story_target_4"];

/**
 * Landing explanation for the intake screen: the Round 1 pain, what SiteDesk does about it, and what
 * a judge can try with one click. It folds into a single line once the user starts working.
 * Honesty rule: Round 1 numbers are shown only as targets and labelled as such.
 */
export default function ProblemValue({ compact, onSample }: { compact: boolean; onSample: (text: string) => void }) {
  const { t } = useI18n();
  const [open, setOpen] = useState(!compact);
  useEffect(() => setOpen(!compact), [compact]);

  return (
    <details className="story" open={open} onToggle={(e) => setOpen(e.currentTarget.open)} data-testid="problem-value">
      <summary className="story-summary">
        <span className="story-summary-title">{open ? t("story_eyebrow") : t("story_compact")}</span>
        <span className="story-summary-toggle">{open ? t("story_hide") : t("story_show")}</span>
      </summary>

      <div className="story-body">
        <h2 className="story-title">{t("story_title")}</h2>
        <p className="story-note">{t("story_title_note")}</p>
        <p className="story-sub">{t("story_sub")}</p>

        <div className="story-pains">
          {PAINS.map(({ icon: Icon, pain, note, fix }) => (
            <article key={pain} className="story-pain">
              <div className="story-pain-head">
                <Icon size={18} aria-hidden />
                <div>
                  <h3>{t(pain)}</h3>
                  <p className="story-pain-note">{t(note)}</p>
                </div>
              </div>
              <p className="story-fix">{t(fix)}</p>
            </article>
          ))}
        </div>

        <div className="story-how" aria-label={t("story_how_title")}>
          <strong className="story-how-title">{t("story_how_title")}</strong>
          <ol>
            {STEPS.map(({ icon: Icon, label, who }) => (
              <li key={label} className={`story-how-step story-how-step--${who}`}>
                <Icon size={16} aria-hidden />
                <span>{t(label)}</span>
                <b className={`story-badge story-badge--${who}`}>{who === "ai" ? t("story_badge_ai") : t("story_badge_you")}</b>
              </li>
            ))}
          </ol>
        </div>

        <div className="story-samples">
          <strong>{t("story_samples_title")}</strong>
          <div className="story-sample-grid">
            {SAMPLE_ORDERS.map((sample) => (
              <button key={sample.id} type="button" className="story-sample" data-testid={`sample-${sample.id}`} onClick={() => onSample(sample.text)}>
                <span className="story-sample-title">{t(sample.title)}</span>
                <span className="story-sample-detail">{t(sample.detail)}</span>
              </button>
            ))}
          </div>
        </div>

        <ul className="story-chips">
          {TRUST.map((key) => (
            <li key={key} className="story-chip">
              <ShieldCheck size={14} aria-hidden /> {t(key)}
            </li>
          ))}
        </ul>

        <details className="story-targets">
          <summary>{t("story_targets_title")}</summary>
          <p>{t("story_targets_note")}</p>
          <ul>
            {TARGETS.map((key) => (
              <li key={key}>{t(key)}</li>
            ))}
          </ul>
        </details>
        <p className="story-sim">{t("story_sim_badge")}</p>
      </div>
    </details>
  );
}
