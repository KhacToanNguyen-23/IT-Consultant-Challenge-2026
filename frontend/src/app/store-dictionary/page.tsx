"use client";

import { useCallback, useEffect, useState } from "react";
import { Loader2, WandSparkles } from "lucide-react";
import { api, ApiError } from "@/client/api";
import { useI18n } from "@/client/i18n";
import { Notice, PosKey, SoftKeys, Terminal, Vfd } from "@/components/pos/Terminal";

interface Mapping {
  id: number;
  normalized_phrase: string;
  mapped_sku: string;
  boost: number;
  active: boolean;
  created_at: string | null;
  deactivated_at: string | null;
}

export default function StoreDictionaryPage() {
  const { t } = useI18n();
  const [items, setItems] = useState<Mapping[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [pendingId, setPendingId] = useState<number | null>(null);
  const [busyId, setBusyId] = useState<number | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await api<{ items: Mapping[] }>("/store-dictionary");
      setItems(result.items);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : t("dictionary_load_error"));
      setItems(null);
    } finally {
      setLoading(false);
    }
  }, [t]);

  useEffect(() => {
    void load();
  }, [load]);

  const deactivate = async (id: number) => {
    setBusyId(id);
    setError(null);
    try {
      await api(`/store-dictionary/${id}`, { method: "DELETE" });
      setPendingId(null);
      await load();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : t("dictionary_update_error"));
    } finally {
      setBusyId(null);
    }
  };

  const formatDate = (date: string | null) => date
    ? new Intl.DateTimeFormat("en-GB", { dateStyle: "medium", timeStyle: "short" }).format(new Date(date))
    : "—";

  return (
    <Terminal
      ticket={
        <div className="paper min-h-full">
          <div className="paper-head">
            <h1 className="paper-title">{t("dictionary_title")}</h1>
            <p className="screen-note mt-1">{t("dictionary_subtitle")}</p>
          </div>
          {error && <div className="px-[18px] pt-4"><Notice tone="bad" alert>{error}</Notice></div>}
          {loading && items === null && <Loader2 className="mx-auto my-12 animate-spin soft" aria-label={t("loading")} />}
          {!error && items?.length === 0 && <p className="px-[18px] py-10 text-center text-base font-semibold">{t("dictionary_empty")}</p>}
          <ul className="m-0 list-none p-0">
            {items?.map((item) => (
              <li key={item.id} className="border-b border-dotted border-[var(--rule)] px-[18px] py-3">
                <div className="grid grid-cols-[minmax(0,1fr)_auto] items-start gap-x-4 gap-y-2">
                  <div className="min-w-0">
                    <p className="m-0 break-words font-semibold">{item.normalized_phrase}</p>
                    <p className="m-0 mt-1 text-sm soft">{item.mapped_sku} · {t("dictionary_boost")} +{Math.round(item.boost * 100)}%</p>
                    <p className="m-0 mt-1 text-xs soft">{t("dictionary_created")}: {formatDate(item.created_at)}</p>
                    {!item.active && <p className="m-0 mt-1 text-xs soft">{t("dictionary_deactivated_at")}: {formatDate(item.deactivated_at)}</p>}
                  </div>
                  <div className="flex flex-wrap items-center justify-end gap-2">
                    <span className={`rounded border px-2 py-1 text-xs font-semibold ${item.active ? "border-emerald-200 bg-emerald-50 text-emerald-800" : "border-slate-200 bg-slate-50 text-slate-600"}`}>
                      {item.active ? t("dictionary_active") : t("dictionary_inactive")}
                    </span>
                    {item.active && (pendingId === item.id ? (
                      <>
                        <button type="button" className="key key--void key--sm !min-h-9 !flex-row" disabled={busyId === item.id} onClick={() => void deactivate(item.id)}>
                          {busyId === item.id ? t("dictionary_deactivating") : t("dictionary_confirm_deactivate")}
                        </button>
                        <button type="button" className="key key--sm !min-h-9 !flex-row" disabled={busyId === item.id} onClick={() => setPendingId(null)}>{t("dictionary_cancel")}</button>
                      </>
                    ) : (
                      <button type="button" className="key key--sm !min-h-9 !flex-row" onClick={() => setPendingId(item.id)}>{t("dictionary_deactivate")}</button>
                    ))}
                  </div>
                </div>
              </li>
            ))}
          </ul>
        </div>
      }
      rail={
        <>
          <Vfd top={t("nav_dictionary")} main={items?.length ?? "--"} sub={t("dictionary_active")} />
          <div className="pos-screen space-y-3">
            <div className="screen-title inline-flex items-center gap-2"><WandSparkles size={18} aria-hidden />{t("nav_dictionary")}</div>
            <p className="screen-note">{t("dictionary_subtitle")}</p>
          </div>
        </>
      }
      keys={
        <SoftKeys slots={[
          <PosKey key="counter" hotkey="F1" href="/" tone="std" icon={<WandSparkles size={17} />}>{t("nav_counter")}</PosKey>,
          null,
          null,
          null,
          null,
          null,
        ]} />
      }
    />
  );
}
