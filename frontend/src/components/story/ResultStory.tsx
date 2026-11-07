"use client";

import Link from "next/link";
import { useI18n } from "@/client/i18n";

/** Keeps one clear next action after the order has been sent or exported. */
export default function ResultStory() {
  const { t } = useI18n();

  return (
    <div className="story-result" data-testid="result-story">
      <Link href="/" className="key key--go story-result-next" data-testid="next-list">
        {t("result_next")}
      </Link>
    </div>
  );
}
