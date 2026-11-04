"use client";

import { Fragment, useRef, useState } from "react";
import type { ChangeEvent, DragEvent, KeyboardEvent } from "react";

const API_URL = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000").replace(/\/+$/, "");
const LOW_CONFIDENCE_THRESHOLD = 0.8;
const ACCEPTED_EXTENSIONS = [".pdf", ".xlsx", ".xls", ".csv"];

type StockStatus = "in_stock" | "out_of_stock";

interface Substitute {
  sku: string;
  name: string;
  confidence: number;
}

interface QuoteItem {
  line_no: number;
  raw_text: string;
  qty: number;
  unit: string;
  matched_sku: string | null;
  matched_name: string | null;
  confidence: number;
  stock_status: StockStatus;
  substitutes: Substitute[] | null;
}

interface ParseResponse {
  quote_id: string;
  processing_time_seconds: number;
  items: QuoteItem[];
}

interface ConfirmResponse {
  order_id: string;
  export_format: string;
  exported_data: unknown;
}

interface LineState {
  line_no: number;
  raw_text: string;
  qty: string;
  unit: string;
  matched_sku: string;
  matched_name: string;
  confidence: number;
  stock_status: StockStatus;
  substitutes: Substitute[];
  final_sku: string;
}

function normalizeConfidence(value: number) {
  if (!Number.isFinite(value)) return 0;
  const normalized = value > 1 ? value / 100 : value;
  return Math.min(Math.max(normalized, 0), 1);
}

function formatConfidence(value: number) {
  return `${Math.round(normalizeConfidence(value) * 100)}%`;
}

function toLineState(item: QuoteItem): LineState {
  const matchedSku = item.matched_sku?.trim() ?? "";
  return {
    line_no: item.line_no,
    raw_text: item.raw_text ?? "",
    qty: item.qty == null ? "" : String(item.qty),
    unit: item.unit ?? "",
    matched_sku: matchedSku,
    matched_name: item.matched_name?.trim() || "No catalog match",
    confidence: normalizeConfidence(item.confidence),
    stock_status: item.stock_status,
    substitutes: Array.isArray(item.substitutes) ? item.substitutes : [],
    final_sku: matchedSku,
  };
}

function formatFileSize(bytes: number) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${Math.round(bytes / 1024)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function formatExportData(data: unknown) {
  if (data == null) return "";
  if (typeof data === "string") return data;
  try {
    return JSON.stringify(data, null, 2);
  } catch {
    return String(data);
  }
}

async function readApiError(res: Response, fallback: string) {
  let detail = "";
  try {
    const raw = await res.text();
    if (raw) {
      try {
        const parsed = JSON.parse(raw) as { detail?: unknown };
        if (parsed && parsed.detail != null) {
          detail =
            typeof parsed.detail === "string"
              ? parsed.detail
              : JSON.stringify(parsed.detail);
        } else {
          detail = raw.slice(0, 200);
        }
      } catch {
        detail = raw.slice(0, 200);
      }
    }
  } catch {
    detail = "";
  }
  return detail ? `${fallback}: ${detail}` : `${fallback} (HTTP ${res.status}).`;
}

function errorMessage(error: unknown, fallback: string) {
  if (error instanceof TypeError) {
    return `Could not reach the backend at ${API_URL}. Make sure the API is running.`;
  }
  return error instanceof Error ? error.message : fallback;
}

export default function Home() {
  const inputRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [rawText, setRawText] = useState("");
  const [dragging, setDragging] = useState(false);
  const [parsing, setParsing] = useState(false);
  const [parseError, setParseError] = useState<string | null>(null);
  const [quote, setQuote] = useState<ParseResponse | null>(null);
  const [lines, setLines] = useState<LineState[]>([]);
  const [expandedLine, setExpandedLine] = useState<number | null>(null);
  const [confirming, setConfirming] = useState(false);
  const [confirmError, setConfirmError] = useState<string | null>(null);
  const [order, setOrder] = useState<ConfirmResponse | null>(null);
  const [copied, setCopied] = useState(false);

  const hasLines = lines.length > 0;
  const outOfStockCount = lines.filter((line) => line.stock_status === "out_of_stock").length;
  const lowConfidenceCount = lines.filter(
    (line) => line.confidence < LOW_CONFIDENCE_THRESHOLD
  ).length;
  const canParse = Boolean(file || rawText.trim());

  const clearFile = () => {
    setFile(null);
    if (inputRef.current) inputRef.current.value = "";
  };

  const acceptFile = (candidate: File) => {
    const lowerName = candidate.name.toLowerCase();
    if (!ACCEPTED_EXTENSIONS.some((extension) => lowerName.endsWith(extension))) {
      setParseError("Unsupported file type. Use PDF, XLSX, XLS or CSV.");
      return;
    }
    setParseError(null);
    setFile(candidate);
    setRawText("");
    setQuote(null);
    setLines([]);
    setExpandedLine(null);
    setOrder(null);
    setConfirmError(null);
    if (inputRef.current) inputRef.current.value = "";
  };

  const handleFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    const candidate = event.target.files?.[0];
    if (candidate) acceptFile(candidate);
  };

  const handleDrop = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setDragging(false);
    const candidate = event.dataTransfer.files?.[0];
    if (candidate) acceptFile(candidate);
  };

  const handleDragOver = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setDragging(true);
  };

  const handleDragLeave = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setDragging(false);
  };

  const handleZoneKeyDown = (event: KeyboardEvent<HTMLDivElement>) => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      inputRef.current?.click();
    }
  };

  const handleRawTextChange = (event: ChangeEvent<HTMLTextAreaElement>) => {
    const value = event.target.value;
    setRawText(value);
    if (value.trim() && file) clearFile();
    if (parseError) setParseError(null);
  };

  const handleParse = async () => {
    if (!canParse) {
      setParseError("Add a PDF/Excel file or paste the raw quote first.");
      return;
    }

    setParsing(true);
    setParseError(null);
    setOrder(null);
    setConfirmError(null);

    try {
      const formData = new FormData();
      if (file) formData.append("file", file);
      if (rawText.trim()) {
        formData.append("text", rawText.trim());
        formData.append("raw_text", rawText.trim());
      }

      const response = await fetch(`${API_URL}/api/quote/parse`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error(await readApiError(response, "Could not parse the quote"));
      }

      const payload = (await response.json()) as ParseResponse;
      if (!payload || !Array.isArray(payload.items)) {
        throw new Error("The parser returned an unexpected response.");
      }

      setQuote(payload);
      setLines(payload.items.map(toLineState));
      setExpandedLine(null);
    } catch (error) {
      setQuote(null);
      setLines([]);
      setParseError(errorMessage(error, "Something went wrong while parsing the quote."));
    } finally {
      setParsing(false);
    }
  };

  const updateQty = (lineNo: number, value: string) => {
    setLines((current) =>
      current.map((line) => (line.line_no === lineNo ? { ...line, qty: value } : line))
    );
  };

  const selectSubstitute = (lineNo: number, sku: string) => {
    setLines((current) =>
      current.map((line) =>
        line.line_no === lineNo ? { ...line, final_sku: sku } : line
      )
    );
  };

  const handleConfirm = async () => {
    if (!quote || !hasLines) return;

    const missingSku = lines.find((line) => !line.final_sku);
    if (missingSku) {
      setConfirmError(
        `Line ${missingSku.line_no} has no matched SKU. Choose a substitute or parse the quote again.`
      );
      return;
    }

    const invalidQty = lines.find((line) => {
      const qty = Number(line.qty);
      return !Number.isFinite(qty) || qty <= 0;
    });
    if (invalidQty) {
      setConfirmError(`Line ${invalidQty.line_no} needs a quantity greater than 0.`);
      return;
    }

    setConfirming(true);
    setConfirmError(null);
    setOrder(null);
    setCopied(false);

    try {
      const response = await fetch(`${API_URL}/api/quote/confirm`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          quote_id: quote.quote_id,
          items: lines.map((line) => ({
            line_no: line.line_no,
            final_sku: line.final_sku,
            qty: Number(line.qty),
          })),
        }),
      });

      if (!response.ok) {
        throw new Error(await readApiError(response, "Could not create the order"));
      }

      const payload = (await response.json()) as ConfirmResponse;
      if (!payload || !payload.order_id) {
        throw new Error("The confirm endpoint returned an unexpected response.");
      }

      setOrder(payload);
    } catch (error) {
      setConfirmError(errorMessage(error, "Something went wrong while creating the order."));
    } finally {
      setConfirming(false);
    }
  };

  const copyExport = async () => {
    if (!order) return;
    try {
      await navigator.clipboard.writeText(formatExportData(order.exported_data));
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1600);
    } catch {
      setCopied(false);
    }
  };

  const resetQuote = () => {
    setQuote(null);
    setLines([]);
    setExpandedLine(null);
    setConfirmError(null);
    setOrder(null);
    setCopied(false);
    setParseError(null);
    setFile(null);
    setRawText("");
    if (inputRef.current) inputRef.current.value = "";
  };

  return (
    <div className="min-h-screen bg-slate-100">
      <header className="sticky top-0 z-30 border-b border-slate-200 bg-white/95 backdrop-blur">
        <div className="mx-auto flex w-full max-w-7xl items-center justify-between gap-4 px-4 py-3 sm:px-6">
          <div className="flex items-center gap-3">
            <div className="grid h-10 w-10 place-items-center rounded-xl bg-emerald-600 text-white shadow-sm">
              <BoxIcon className="h-5 w-5" />
            </div>
            <div>
              <p className="text-base font-bold tracking-tight text-slate-900">SiteDesk</p>
              <p className="text-xs text-slate-500">Trade counter assistant</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span className="hidden items-center gap-1.5 rounded-full border border-slate-200 bg-slate-50 px-2.5 py-1 text-xs font-medium text-slate-600 sm:inline-flex">
              <SparkleIcon className="h-3.5 w-3.5 text-emerald-600" />
              AI quote intake
            </span>
            <span className="inline-flex items-center gap-1.5 rounded-full border border-emerald-200 bg-emerald-50 px-2.5 py-1 text-xs font-semibold text-emerald-700">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
              MVP
            </span>
          </div>
        </div>
      </header>

      <main className="mx-auto w-full max-w-7xl px-4 py-6 sm:px-6 lg:py-8">
        <div className="mb-6">
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 sm:text-3xl">
            From material list to confirmed order
          </h1>
          <p className="mt-1.5 max-w-3xl text-sm text-slate-600">
            Drop in a PDF or Excel quote. Review the AI matches, resolve stock-outs with
            substitutes, then push the order to your POS.
          </p>
        </div>

        <section className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
          <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-200 px-5 py-4">
            <div className="flex items-center gap-3">
              <span className="grid h-7 w-7 place-items-center rounded-full bg-slate-900 text-xs font-bold text-white">
                1
              </span>
              <div>
                <h2 className="text-sm font-semibold text-slate-900">Add the customer quote</h2>
                <p className="text-xs text-slate-500">
                  Upload a file or paste the raw list, then parse it with AI.
                </p>
              </div>
            </div>
            <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">
              Intake
            </span>
          </div>

          <div className="grid gap-4 p-5 md:grid-cols-2">
            <div
              role="button"
              tabIndex={0}
              aria-label="Upload a PDF or Excel quote"
              onClick={() => inputRef.current?.click()}
              onKeyDown={handleZoneKeyDown}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              className={`flex min-h-[190px] cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed px-4 py-6 text-center transition focus:outline-none focus:ring-2 focus:ring-emerald-500/40 ${
                dragging
                  ? "border-emerald-500 bg-emerald-50"
                  : file
                    ? "border-emerald-300 bg-emerald-50/40"
                    : "border-slate-300 bg-slate-50 hover:border-emerald-400 hover:bg-emerald-50/30"
              }`}
            >
              <input
                ref={inputRef}
                type="file"
                accept=".pdf,.xlsx,.xls,.csv,application/pdf,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,application/vnd.ms-excel,text/csv"
                onChange={handleFileChange}
                className="hidden"
              />
              {file ? (
                <>
                  <div className="grid h-12 w-12 place-items-center rounded-full bg-white text-emerald-600 shadow-sm ring-1 ring-emerald-100">
                    <FileIcon className="h-6 w-6" />
                  </div>
                  <p className="mt-3 max-w-full truncate text-sm font-semibold text-slate-900">
                    {file.name}
                  </p>
                  <p className="mt-0.5 text-xs text-slate-500">
                    {formatFileSize(file.size)} · click to replace
                  </p>
                  <button
                    type="button"
                    onClick={(event) => {
                      event.stopPropagation();
                      clearFile();
                    }}
                    className="mt-3 inline-flex items-center gap-1 rounded-md border border-slate-300 bg-white px-2.5 py-1.5 text-xs font-semibold text-slate-600 shadow-sm hover:bg-slate-50"
                  >
                    <XIcon className="h-3.5 w-3.5" />
                    Remove file
                  </button>
                </>
              ) : (
                <>
                  <div className="grid h-12 w-12 place-items-center rounded-full bg-white text-slate-500 shadow-sm ring-1 ring-slate-200">
                    <UploadIcon className="h-6 w-6" />
                  </div>
                  <p className="mt-3 text-sm font-semibold text-slate-900">
                    Drag &amp; drop your order file
                  </p>
                  <p className="mt-0.5 text-xs text-slate-500">
                    or click anywhere in this box to browse
                  </p>
                  <p className="mt-2 text-[11px] font-semibold uppercase tracking-wide text-slate-400">
                    PDF · XLSX · XLS · CSV
                  </p>
                </>
              )}
            </div>

            <div className="flex flex-col">
              <label htmlFor="raw-text" className="text-sm font-semibold text-slate-900">
                Or paste the raw text
              </label>
              <p className="text-xs text-slate-500">
                Fallback for unreadable files or quick phone orders.
              </p>
              <textarea
                id="raw-text"
                value={rawText}
                onChange={handleRawTextChange}
                placeholder={
                  "e.g.\n20 x 2x4 timber 4.8m\n5 bags cement 25kg\n12 sheets plywood 12mm"
                }
                className="mt-2 min-h-[150px] flex-1 resize-none rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm leading-6 text-slate-900 placeholder:text-slate-400 focus:border-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/20"
              />
            </div>
          </div>

          {parseError && (
            <div
              role="alert"
              className="mx-5 mb-4 flex items-start gap-2 rounded-lg border border-red-200 bg-red-50 px-3 py-2.5 text-sm text-red-700"
            >
              <AlertIcon className="mt-0.5 h-4 w-4 shrink-0" />
              <span>{parseError}</span>
            </div>
          )}

          <div className="flex flex-col gap-3 border-t border-slate-200 bg-slate-50/70 px-5 py-4 sm:flex-row sm:items-center sm:justify-between">
            <p className="text-xs leading-5 text-slate-500">
              Each line is matched against the internal catalog. Rows below 80% confidence
              are highlighted for review.
            </p>
            <button
              type="button"
              onClick={handleParse}
              disabled={parsing || !canParse}
              className="inline-flex shrink-0 items-center justify-center gap-2 rounded-lg bg-emerald-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-emerald-700 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:bg-slate-300 disabled:text-slate-500"
            >
              {parsing ? (
                <SpinnerIcon className="h-4 w-4 animate-spin" />
              ) : (
                <SparkleIcon className="h-4 w-4" />
              )}
              {parsing ? "Parsing list…" : "Parse quote"}
            </button>
          </div>
        </section>

        <section id="results" className="mt-6">
          <div className="mb-3 flex flex-wrap items-end justify-between gap-3">
            <div className="flex items-center gap-3">
              <span
                className={`grid h-7 w-7 place-items-center rounded-full text-xs font-bold ${
                  quote ? "bg-slate-900 text-white" : "bg-slate-200 text-slate-500"
                }`}
              >
                2
              </span>
              <div>
                <h2 className="text-sm font-semibold text-slate-900">Review matched items</h2>
                <p className="text-xs text-slate-500">
                  Verify low-confidence matches and resolve stock-outs before creating the order.
                </p>
              </div>
            </div>
            {quote && (
              <div className="flex flex-wrap items-center gap-2">
                <span className="inline-flex items-center rounded-full border border-slate-200 bg-white px-2.5 py-1 font-mono text-[11px] font-medium text-slate-600">
                  Quote {quote.quote_id}
                </span>
                {Number.isFinite(quote.processing_time_seconds) && (
                  <span className="inline-flex items-center rounded-full border border-slate-200 bg-white px-2.5 py-1 text-[11px] font-medium text-slate-600">
                    Parsed in {quote.processing_time_seconds.toFixed(1)}s
                  </span>
                )}
                <button
                  type="button"
                  onClick={resetQuote}
                  className="rounded-md border border-slate-300 bg-white px-2.5 py-1 text-[11px] font-semibold text-slate-600 shadow-sm hover:bg-slate-50"
                >
                  New quote
                </button>
              </div>
            )}
          </div>

          {!quote ? (
            <div className="rounded-xl border border-slate-200 bg-white px-6 py-12 text-center shadow-sm">
              <div className="mx-auto grid h-12 w-12 place-items-center rounded-full bg-slate-100 text-slate-400">
                <TableIcon className="h-6 w-6" />
              </div>
              <h3 className="mt-3 text-sm font-semibold text-slate-900">
                No quote parsed yet
              </h3>
              <p className="mx-auto mt-1 max-w-md text-sm text-slate-500">
                Your matched items, stock badges and substitute suggestions will appear here
                after you parse a file or text list.
              </p>
            </div>
          ) : lines.length === 0 ? (
            <div className="rounded-xl border border-slate-200 bg-white px-6 py-12 text-center shadow-sm">
              <div className="mx-auto grid h-12 w-12 place-items-center rounded-full bg-amber-100 text-amber-600">
                <AlertIcon className="h-6 w-6" />
              </div>
              <h3 className="mt-3 text-sm font-semibold text-slate-900">No items found</h3>
              <p className="mx-auto mt-1 max-w-md text-sm text-slate-500">
                The parser did not return any line items. Try a clearer file or paste the list
                as plain text.
              </p>
              <button
                type="button"
                onClick={resetQuote}
                className="mt-4 rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm font-semibold text-slate-700 shadow-sm hover:bg-slate-50"
              >
                Try another quote
              </button>
            </div>
          ) : (
            <>
              <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
                <div className="flex flex-wrap items-center gap-x-5 gap-y-2 border-b border-slate-200 bg-slate-50/80 px-4 py-2.5 text-xs">
                  <span className="text-slate-600">
                    <span className="font-bold text-slate-900">{lines.length}</span> items
                  </span>
                  <span className="text-red-700">
                    <span className="font-bold">{outOfStockCount}</span> out of stock
                  </span>
                  <span className="text-amber-800">
                    <span className="font-bold">{lowConfidenceCount}</span> low-confidence
                  </span>
                  <span className="ml-auto inline-flex items-center gap-1.5 text-slate-500">
                    <span className="h-2 w-2 rounded-sm bg-amber-300" />
                    Yellow rows need a quick check
                  </span>
                </div>

                <div className="overflow-x-auto">
                  <table className="w-full min-w-[900px] text-left text-sm">
                    <thead className="bg-white text-[11px] uppercase tracking-wider text-slate-500">
                      <tr className="border-b border-slate-200">
                        <th scope="col" className="w-12 px-4 py-3 font-semibold">
                          #
                        </th>
                        <th scope="col" className="px-4 py-3 font-semibold">
                          Original name
                        </th>
                        <th scope="col" className="px-4 py-3 font-semibold">
                          Matched SKU &amp; name
                        </th>
                        <th scope="col" className="w-36 px-4 py-3 font-semibold">
                          Qty / unit
                        </th>
                        <th scope="col" className="w-36 px-4 py-3 font-semibold">
                          Stock
                        </th>
                        <th scope="col" className="w-40 px-4 py-3 text-right font-semibold">
                          Substitutes
                        </th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {lines.map((line) => {
                        const lowConfidence = line.confidence < LOW_CONFIDENCE_THRESHOLD;
                        const isOutOfStock = line.stock_status === "out_of_stock";
                        const isExpanded = expandedLine === line.line_no;
                        const selectedSubstitute = line.substitutes.find(
                          (substitute) => substitute.sku === line.final_sku
                        );
                        const usingSubstitute =
                          Boolean(line.final_sku) && line.final_sku !== line.matched_sku;

                        return (
                          <Fragment key={line.line_no}>
                            <tr
                              className={
                                lowConfidence
                                  ? "bg-amber-50 hover:bg-amber-100/80"
                                  : "bg-white hover:bg-slate-50"
                              }
                            >
                              <td
                                className={`px-4 py-3 align-top text-sm text-slate-400 ${
                                  lowConfidence ? "border-l-4 border-l-amber-400" : ""
                                }`}
                              >
                                {line.line_no}
                              </td>
                              <td className="px-4 py-3 align-top">
                                <p className="font-medium leading-5 text-slate-900">
                                  {line.raw_text || "—"}
                                </p>
                                {lowConfidence && (
                                  <p className="mt-1 inline-flex items-center gap-1 text-[11px] font-semibold text-amber-700">
                                    <AlertIcon className="h-3 w-3" />
                                    Check this match
                                  </p>
                                )}
                              </td>
                              <td className="px-4 py-3 align-top">
                                <div className="flex flex-wrap items-center gap-1.5">
                                  <span className="font-mono text-xs font-semibold text-slate-800">
                                    {line.matched_sku || "UNMATCHED"}
                                  </span>
                                  <span
                                    className={`rounded px-1.5 py-0.5 text-[11px] font-semibold ${
                                      lowConfidence
                                        ? "bg-amber-100 text-amber-800"
                                        : "bg-emerald-50 text-emerald-700"
                                    }`}
                                  >
                                    {formatConfidence(line.confidence)} match
                                  </span>
                                </div>
                                <p className="mt-0.5 leading-5 text-slate-700">
                                  {line.matched_name}
                                </p>
                                {usingSubstitute && (
                                  <p className="mt-1 text-xs font-medium text-emerald-700">
                                    Substitute selected:{" "}
                                    {selectedSubstitute?.name ?? line.final_sku}{" "}
                                    <span className="font-mono">({line.final_sku})</span>
                                  </p>
                                )}
                              </td>
                              <td className="px-4 py-3 align-top">
                                <div className="flex items-center gap-1.5">
                                  <input
                                    type="number"
                                    min="0"
                                    step="any"
                                    inputMode="decimal"
                                    aria-label={`Quantity for line ${line.line_no}`}
                                    value={line.qty}
                                    onChange={(event) =>
                                      updateQty(line.line_no, event.target.value)
                                    }
                                    className="w-20 rounded-md border border-slate-300 bg-white px-2 py-1.5 text-right text-sm text-slate-900 focus:border-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/20"
                                  />
                                  <span className="text-xs text-slate-500">
                                    {line.unit || "unit"}
                                  </span>
                                </div>
                              </td>
                              <td className="px-4 py-3 align-top">
                                <StockBadge status={line.stock_status} />
                              </td>
                              <td className="px-4 py-3 text-right align-top">
                                {isOutOfStock ? (
                                  <button
                                    type="button"
                                    onClick={() =>
                                      setExpandedLine((current) =>
                                        current === line.line_no ? null : line.line_no
                                      )
                                    }
                                    aria-expanded={isExpanded}
                                    className={`inline-flex items-center gap-1 rounded-md border px-2.5 py-1.5 text-xs font-semibold shadow-sm transition ${
                                      isExpanded
                                        ? "border-slate-400 bg-slate-100 text-slate-800"
                                        : "border-slate-300 bg-white text-slate-700 hover:bg-slate-50"
                                    }`}
                                  >
                                    {isExpanded ? "Hide" : "View substitutes"}
                                    {line.substitutes.length > 0 && (
                                      <span className="rounded-full bg-slate-200 px-1.5 py-0.5 text-[10px] text-slate-600">
                                        {line.substitutes.length}
                                      </span>
                                    )}
                                    <ChevronIcon
                                      className={`h-3.5 w-3.5 transition-transform ${
                                        isExpanded ? "rotate-180" : ""
                                      }`}
                                    />
                                  </button>
                                ) : (
                                  <span className="text-slate-300">—</span>
                                )}
                              </td>
                            </tr>

                            {isOutOfStock && isExpanded && (
                              <tr className="bg-slate-50/80">
                                <td colSpan={6} className="px-4 pb-4 pt-1">
                                  <div className="rounded-lg border border-slate-200 bg-white p-4">
                                    <div className="flex flex-wrap items-start justify-between gap-3">
                                      <div>
                                        <p className="text-sm font-semibold text-slate-900">
                                          Suggested substitutes
                                        </p>
                                        <p className="text-xs text-slate-500">
                                          Returned with this quote — no extra lookup needed.
                                        </p>
                                      </div>
                                      {line.matched_sku && (
                                        <button
                                          type="button"
                                          onClick={() =>
                                            selectSubstitute(line.line_no, line.matched_sku)
                                          }
                                          className="rounded-md border border-slate-300 bg-white px-2.5 py-1.5 text-xs font-semibold text-slate-600 shadow-sm hover:bg-slate-50"
                                        >
                                          Keep original {line.matched_sku}
                                        </button>
                                      )}
                                    </div>

                                    {line.substitutes.length === 0 ? (
                                      <p className="mt-3 rounded-md border border-dashed border-slate-200 bg-slate-50 px-3 py-4 text-sm text-slate-500">
                                        No substitutes were returned for this line.
                                      </p>
                                    ) : (
                                      <div className="mt-3 grid gap-2 sm:grid-cols-2">
                                        {line.substitutes.map((substitute) => {
                                          const selected = line.final_sku === substitute.sku;
                                          return (
                                            <button
                                              key={substitute.sku}
                                              type="button"
                                              onClick={() =>
                                                selectSubstitute(line.line_no, substitute.sku)
                                              }
                                              aria-pressed={selected}
                                              className={`rounded-lg border p-3 text-left shadow-sm transition ${
                                                selected
                                                  ? "border-emerald-400 bg-emerald-50 ring-1 ring-emerald-200"
                                                  : "border-slate-200 bg-white hover:border-emerald-300 hover:bg-emerald-50/40"
                                              }`}
                                            >
                                              <div className="flex items-center justify-between gap-2">
                                                <span className="font-mono text-xs font-semibold text-slate-800">
                                                  {substitute.sku}
                                                </span>
                                                <span className="rounded bg-slate-100 px-1.5 py-0.5 text-[11px] font-semibold text-slate-600">
                                                  {formatConfidence(substitute.confidence)}{" "}
                                                  match
                                                </span>
                                              </div>
                                              <p className="mt-1 text-sm font-medium leading-5 text-slate-900">
                                                {substitute.name}
                                              </p>
                                              <p
                                                className={`mt-2 text-xs font-semibold ${
                                                  selected
                                                    ? "text-emerald-700"
                                                    : "text-slate-500"
                                                }`}
                                              >
                                                {selected
                                                  ? "Selected for this order"
                                                  : "Use this substitute"}
                                              </p>
                                            </button>
                                          );
                                        })}
                                      </div>
                                    )}
                                  </div>
                                </td>
                              </tr>
                            )}
                          </Fragment>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>

              <div className="mt-4 rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
                <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                  <div>
                    <p className="text-sm font-semibold text-slate-900">
                      Ready to push to POS?
                    </p>
                    <p className="mt-0.5 text-xs text-slate-500">
                      {lines.length} items · {outOfStockCount} out of stock ·{" "}
                      {lowConfidenceCount} low-confidence
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={handleConfirm}
                    disabled={confirming || !hasLines}
                    className="inline-flex items-center justify-center gap-2 rounded-lg bg-slate-900 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-slate-800 focus:outline-none focus:ring-2 focus:ring-slate-700 focus:ring-offset-2 disabled:cursor-not-allowed disabled:bg-slate-300 disabled:text-slate-500"
                  >
                    {confirming ? (
                      <SpinnerIcon className="h-4 w-4 animate-spin" />
                    ) : (
                      <ArrowRightIcon className="h-4 w-4" />
                    )}
                    {confirming ? "Creating order…" : "Create order"}
                  </button>
                </div>
                {confirmError && (
                  <div
                    role="alert"
                    className="mt-3 flex items-start gap-2 rounded-lg border border-red-200 bg-red-50 px-3 py-2.5 text-sm text-red-700"
                  >
                    <AlertIcon className="mt-0.5 h-4 w-4 shrink-0" />
                    <span>{confirmError}</span>
                  </div>
                )}
              </div>

              {order && (
                <div className="mt-4 overflow-hidden rounded-xl border border-emerald-200 bg-emerald-50 shadow-sm">
                  <div className="flex flex-wrap items-start justify-between gap-3 px-5 py-4">
                    <div className="flex items-start gap-3">
                      <div className="grid h-9 w-9 shrink-0 place-items-center rounded-full bg-emerald-600 text-white">
                        <CheckIcon className="h-5 w-5" />
                      </div>
                      <div>
                        <p className="text-sm font-semibold text-emerald-900">Order created</p>
                        <p className="mt-0.5 text-xs text-emerald-700">
                          Order{" "}
                          <span className="font-mono font-semibold">{order.order_id}</span> ·
                          export format{" "}
                          <span className="font-mono font-semibold uppercase">
                            {order.export_format}
                          </span>
                        </p>
                      </div>
                    </div>
                    <button
                      type="button"
                      onClick={copyExport}
                      className="inline-flex items-center gap-1.5 rounded-md border border-emerald-300 bg-white px-2.5 py-1.5 text-xs font-semibold text-emerald-700 shadow-sm hover:bg-emerald-50"
                    >
                      {copied ? (
                        <CheckIcon className="h-3.5 w-3.5" />
                      ) : (
                        <CopyIcon className="h-3.5 w-3.5" />
                      )}
                      {copied ? "Copied" : "Copy export"}
                    </button>
                  </div>
                  <div className="border-t border-emerald-200/70 px-5 py-3">
                    <p className="mb-1.5 text-[11px] font-semibold uppercase tracking-wider text-emerald-700">
                      Export payload
                    </p>
                    <pre className="max-h-64 overflow-auto rounded-lg bg-slate-900 p-3 text-xs leading-5 text-slate-100">
                      {formatExportData(order.exported_data) || "No export data returned."}
                    </pre>
                  </div>
                </div>
              )}
            </>
          )}
        </section>
      </main>

      <footer className="border-t border-slate-200 py-5 text-center text-xs text-slate-400">
        SiteDesk MVP · Quote intake, SKU matching and POS hand-off for Company A.
      </footer>
    </div>
  );
}

function StockBadge({ status }: { status: StockStatus }) {
  const isOutOfStock = status === "out_of_stock";
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-semibold ${
        isOutOfStock
          ? "border-red-200 bg-red-50 text-red-700"
          : "border-emerald-200 bg-emerald-50 text-emerald-700"
      }`}
    >
      <span
        className={`h-1.5 w-1.5 rounded-full ${
          isOutOfStock ? "bg-red-500" : "bg-emerald-500"
        }`}
      />
      {isOutOfStock ? "Out of stock" : "In stock"}
    </span>
  );
}

function UploadIcon({ className = "h-5 w-5" }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden="true"
    >
      <path d="M12 16V4m0 0L7 9m5-5 5 5" />
      <path d="M4 16v2a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-2" />
    </svg>
  );
}

function FileIcon({ className = "h-5 w-5" }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden="true"
    >
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
      <path d="M14 2v6h6" />
      <path d="M8 13h8M8 17h5" />
    </svg>
  );
}

function TableIcon({ className = "h-5 w-5" }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden="true"
    >
      <rect x="3" y="4" width="18" height="16" rx="2" />
      <path d="M3 10h18M9 10v10" />
    </svg>
  );
}

function SparkleIcon({ className = "h-5 w-5" }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden="true"
    >
      <path d="M12 3v4M12 17v4M3 12h4M17 12h4" />
      <path d="m5.6 5.6 2.8 2.8M15.6 15.6l2.8 2.8M18.4 5.6l-2.8 2.8M8.4 15.6l-2.8 2.8" />
    </svg>
  );
}

function SpinnerIcon({ className = "h-5 w-5" }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" className={className} aria-hidden="true">
      <circle
        cx="12"
        cy="12"
        r="9"
        stroke="currentColor"
        strokeWidth="2.5"
        strokeOpacity="0.25"
      />
      <path
        d="M21 12a9 9 0 0 0-9-9"
        stroke="currentColor"
        strokeWidth="2.5"
        strokeLinecap="round"
      />
    </svg>
  );
}

function ChevronIcon({ className = "h-4 w-4" }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden="true"
    >
      <path d="m6 9 6 6 6-6" />
    </svg>
  );
}

function AlertIcon({ className = "h-5 w-5" }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden="true"
    >
      <path d="M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0Z" />
      <path d="M12 9v4M12 17h.01" />
    </svg>
  );
}

function CheckIcon({ className = "h-5 w-5" }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden="true"
    >
      <path d="m5 12 5 5L20 7" />
    </svg>
  );
}

function XIcon({ className = "h-4 w-4" }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden="true"
    >
      <path d="M18 6 6 18M6 6l12 12" />
    </svg>
  );
}

function ArrowRightIcon({ className = "h-5 w-5" }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden="true"
    >
      <path d="M5 12h14m-6-6 6 6-6 6" />
    </svg>
  );
}

function CopyIcon({ className = "h-4 w-4" }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden="true"
    >
      <rect x="9" y="9" width="12" height="12" rx="2" />
      <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
    </svg>
  );
}

function BoxIcon({ className = "h-5 w-5" }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden="true"
    >
      <path d="m21 8-9-5-9 5 9 5 9-5Z" />
      <path d="M3 8v8l9 5 9-5V8" />
      <path d="M12 13v8" />
    </svg>
  );
}
