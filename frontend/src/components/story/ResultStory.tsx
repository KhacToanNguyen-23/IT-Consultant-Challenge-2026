"use client";

import Link from "next/link";
import { useI18n } from "@/client/i18n";
import type { SessionView } from "@/client/api";

/** Under the receipt: what happened in plain words, the real time against the Round 1 target, and the next action. */
export default function ResultStory({ session }: { session: SessionView }) {
  const { t } = useI18n();
  const c = session.confirmation;
  const ok = c.order_status === "POS_ACCEPTED";

  return (
    <div className="story-result" data-testid="result-story">
      <p className={ok ? "story-result-ok" : "story-result-csv"}>{ok ? t("result_story_ok") : t("result_story_csv")}</p>
      <p>{t("result_audit")}</p>
      <Link href="/" className="key key--go story-result-next" data-testid="next-list">
        {t("result_next")}
      </Link>
    </div>
  );
}
