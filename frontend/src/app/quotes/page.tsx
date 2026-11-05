"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { Loader2, Mail, Search } from "lucide-react";
import { api, ApiError, fmtTime } from "@/client/api";
import { useI18n } from "@/client/i18n";
import { Notice, PosKey, SoftKeys, Terminal, Vfd } from "@/components/pos/Terminal";
import { StatePill } from "@/components/StatusBadge";

interface Item {
  quote_id: string;
  status: string;
  client_id: string;
  valid_until: string;
  line_count: number;
  created_at: string;
  customer_confirmed: boolean;
}

const STATUSES = ["", "SAVED", "SENT", "PREPARING", "CONFIRMED", "EXPIRED", "CANCELLED"];

export default function QuotesPage() {
  const { t, lang } = useI18n();
  const [items, setItems] = useState<Item[] | null>(null);
  const [q, setQ] = useState("");
  const [status, setStatus] = useState("");
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async (query = "", st = "") => {
    setError(null);
    try {
      const p = new URLSearchParams();
      if (query.trim()) p.set("q", query.trim());
      if (st) p.set("status", st);
      setItems((await api<{ items: Item[] }>(`/quotes?${p}`)).items);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : String(e));
      setItems([]);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load, lang]);

  return (
    <Terminal
      ticket={
        <div className="paper min-h-full">
          <div className="paper-head">
            <h1 className="paper-title">{t("quotes_title")}</h1>
            <p className="mt-1 text-sm soft">{t("quotes_sub")}</p>
          </div>
          {items === null && <Loader2 className="mx-auto my-12 animate-spin soft" aria-label={t("loading")} />}
          {items?.length === 0 && <p className="px-[18px] py-10 text-center text-base font-semibold">{t("no_quotes")}</p>}
          <ul>
            {items?.map((i) => (
              <li key={i.quote_id} className="border-b border-dotted border-[var(--rule)]">
                <Link href={`/quotes/${i.quote_id}`} className="grid grid-cols-[minmax(0,1fr)_auto] gap-x-4 gap-y-1 px-[18px] py-3 hover:bg-[#f3f2ea]" style={{ outlineOffset: -3 }}>
                  <span className="min-w-0">
                    <span className="font-mono text-base font-semibold">{i.quote_id}</span> <StatePill status={i.status} />
                  </span>
                  <span className="font-mono text-right tabular">
                    {t("valid_until")}: {i.valid_until}
                  </span>
                  <span className="text-sm soft">
                    {t("client")} {i.client_id}, {t("n_lines", { n: i.line_count })}, {t("col_created")} {fmtTime(i.created_at)}
                  </span>
                  <span className="text-right text-sm font-semibold">{i.customer_confirmed && `${t("col_cust_conf")} ${t("yes")}`}</span>
                </Link>
              </li>
            ))}
          </ul>
        </div>
      }
      rail={
        <>
          <Vfd top={t("vfd_quotes")} main={items?.length ?? "--"} />
          <div className="pos-screen space-y-3">
            <form
              onSubmit={(e) => {
                e.preventDefault();
                load(q, status);
              }}
            >
              <label className="block font-semibold">
                {t("col_id")}
                <input value={q} onChange={(e) => setQ(e.target.value)} placeholder={t("quote_id_ph")} className="field mt-1 font-normal" />
              </label>
            </form>
            <div role="group" aria-label={t("filter_status")}>
              <div className="mb-1.5 font-semibold">{t("filter_status")}</div>
              <div className="grid grid-cols-2 gap-1.5">
                {STATUSES.map((st) => (
                  <button
                    key={st}
                    type="button"
                    aria-pressed={status === st}
                    onClick={() => {
                      setStatus(st);
                      load(q, st);
                    }}
                    className="tile font-semibold first:col-span-2"
                  >
                    {st || t("all_statuses")}
                  </button>
                ))}
              </div>
            </div>
            {error && (
              <Notice tone="bad" alert>
                {error}
              </Notice>
            )}
          </div>
        </>
      }
      keys={
        <SoftKeys
          slots={[
            <PosKey key="email" hotkey="F3" tone="quote" icon={<Mail size={17} />} href="/?mode=email">
              {t("key_new_email")}
            </PosKey>,
            null,
            null,
            null,
            null,
            <PosKey key="search" hotkey="F9" tone="nav" icon={<Search size={17} />} onClick={() => load(q, status)}>
              {t("key_search")}
            </PosKey>,
          ]}
        />
      }
    />
  );
}
