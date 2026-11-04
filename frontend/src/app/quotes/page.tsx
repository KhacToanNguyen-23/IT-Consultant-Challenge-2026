"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { Loader2, Mail, Search } from "lucide-react";
import { api, ApiError, fmtTime } from "@/client/api";
import { useI18n } from "@/client/i18n";
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
    <div className="space-y-4">
      <div className="flex flex-wrap items-end gap-3">
        <div>
          <h1 className="text-xl font-bold">{t("quotes_title")}</h1>
          <p className="text-sm text-slate-600">{t("quotes_sub")}</p>
        </div>
        <Link href="/" className="ml-auto inline-flex items-center gap-2 rounded-md bg-violet-700 px-3 py-2 text-sm font-semibold text-white hover:bg-violet-800">
          <Mail size={16} /> {t("new_email")}
        </Link>
      </div>

      <form
        className="flex flex-wrap gap-2"
        onSubmit={(e) => {
          e.preventDefault();
          load(q, status);
        }}
      >
        <input value={q} onChange={(e) => setQ(e.target.value)} placeholder={t("quote_id_ph")} className="w-64 rounded border border-slate-300 bg-white px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-600" />
        <select
          value={status}
          onChange={(e) => {
            setStatus(e.target.value);
            load(q, e.target.value);
          }}
          className="rounded border border-slate-300 bg-white px-2 py-1.5 text-sm"
        >
          {STATUSES.map((s) => (
            <option key={s} value={s}>
              {s || t("all_statuses")}
            </option>
          ))}
        </select>
        <button type="submit" className="inline-flex items-center gap-1 rounded border border-slate-300 bg-white px-3 py-1.5 text-sm font-semibold hover:bg-slate-50">
          <Search size={14} /> {t("search")}
        </button>
      </form>

      {error && (
        <p role="alert" className="rounded-md border border-red-300 bg-red-50 px-3 py-2 text-sm text-red-900">
          {error}
        </p>
      )}

      <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white shadow-sm">
        <table className="w-full min-w-[700px] text-sm">
          <thead className="bg-slate-50 text-left text-xs uppercase tracking-wide text-slate-500">
            <tr>
              <th className="px-3 py-2">{t("col_id")}</th>
              <th className="px-3 py-2">{t("status")}</th>
              <th className="px-3 py-2">{t("client")}</th>
              <th className="px-3 py-2">{t("col_lines")}</th>
              <th className="px-3 py-2">{t("valid_until")}</th>
              <th className="px-3 py-2">{t("col_cust_conf")}</th>
              <th className="px-3 py-2">{t("col_created")}</th>
            </tr>
          </thead>
          <tbody>
            {items === null && (
              <tr>
                <td colSpan={7} className="py-10 text-center">
                  <Loader2 className="mx-auto animate-spin text-slate-400" />
                </td>
              </tr>
            )}
            {items?.length === 0 && (
              <tr>
                <td colSpan={7} className="py-10 text-center text-slate-500">
                  {t("no_quotes")}
                </td>
              </tr>
            )}
            {items?.map((i) => (
              <tr key={i.quote_id} className="border-t border-slate-100 hover:bg-slate-50">
                <td className="px-3 py-2">
                  <Link href={`/quotes/${i.quote_id}`} className="font-mono font-semibold text-blue-800 hover:underline">
                    {i.quote_id}
                  </Link>
                </td>
                <td className="px-3 py-2">
                  <StatePill status={i.status} />
                </td>
                <td className="px-3 py-2">{i.client_id}</td>
                <td className="px-3 py-2 tabular">{i.line_count}</td>
                <td className="px-3 py-2 tabular">{i.valid_until}</td>
                <td className="px-3 py-2">{i.customer_confirmed ? t("yes") : "—"}</td>
                <td className="px-3 py-2 tabular text-slate-500">{fmtTime(i.created_at)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
