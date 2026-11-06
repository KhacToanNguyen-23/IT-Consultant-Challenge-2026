"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { Loader2, Mail, Search } from "lucide-react";
import { api, ApiError } from "@/client/api";
import { useI18n } from "@/client/i18n";
import { Notice, PosKey, SoftKeys, Terminal, Vfd } from "@/components/pos/Terminal";
import { StatePill } from "@/components/StatusBadge";
import ListPagination from "@/components/pos/ListPagination";

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
const PAGE_SIZE = 10;

export default function QuotesPage() {
  const { t, lang } = useI18n();
  const [items, setItems] = useState<Item[] | null>(null);
  const [q, setQ] = useState("");
  const [status, setStatus] = useState("");
  const [page, setPage] = useState(0);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async (query = "", st = "") => {
    setError(null);
    try {
      const p = new URLSearchParams();
      if (query.trim()) p.set("q", query.trim());
      if (st) p.set("status", st);
      setItems((await api<{ items: Item[] }>(`/quotes?${p}`)).items);
      setPage(0);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : String(e));
      setItems([]);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load, lang]);

  const pageItems = items?.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE);

  return (
    <Terminal
      ticket={
        <div className="paper paper--quotes min-h-full">
          <div className="paper-head">
            <h1 className="paper-title">{t("quotes_title")}</h1>
          </div>
          {items === null && <Loader2 className="mx-auto my-12 animate-spin soft" aria-label={t("loading")} />}
          {items?.length === 0 && <p className="px-[18px] py-10 text-center text-base font-semibold">{t("no_quotes")}</p>}
          <ul>
            {pageItems?.map((i) => (
              <li key={i.quote_id} className="border-b border-dotted border-[var(--rule)]">
                <Link href={`/quotes/${i.quote_id}`} className="grid grid-cols-[minmax(0,1fr)_auto] gap-x-4 gap-y-1 px-[18px] py-3 hover:bg-[#f3f2ea]" style={{ outlineOffset: -3 }}>
                  <span className="min-w-0">
                    <span className="font-mono text-base font-semibold">{i.quote_id}</span> <StatePill status={i.status} />
                  </span>
                  <span className="font-mono text-right tabular">
                    {t("valid_until")}: {i.valid_until}
                  </span>
                  <span className="text-sm soft">{t("client")} {i.client_id} · {t("n_lines", { n: i.line_count })}</span>
                  <span className="text-right text-sm font-semibold">{i.customer_confirmed && `${t("col_cust_conf")} ${t("yes")}`}</span>
                </Link>
              </li>
            ))}
          </ul>
          <ListPagination total={items?.length ?? 0} page={page} pageSize={PAGE_SIZE} onPageChange={setPage} />
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
                <div className="mt-1 flex gap-2">
                  <input value={q} onChange={(e) => setQ(e.target.value)} placeholder={t("quote_id_ph")} className="field min-w-0 flex-1 font-normal" />
                  <button type="submit" className="key key--nav key--sm flex-none !flex-row !items-center gap-1.5">
                    <Search size={15} aria-hidden /> {t("key_search")}
                  </button>
                </div>
              </label>
            </form>
            <label className="block font-semibold">
              {t("filter_status")}
              <select value={status} onChange={(e) => { setStatus(e.target.value); load(q, e.target.value); }} className="field mt-1 font-normal">
                {STATUSES.map((st) => <option key={st} value={st}>{st || t("all_statuses")}</option>)}
              </select>
            </label>
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
            null,
          ]}
        />
      }
    />
  );
}
