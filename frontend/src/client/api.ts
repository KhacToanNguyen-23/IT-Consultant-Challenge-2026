export const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export class ApiError extends Error {
  code: string;
  details: Record<string, unknown>;
  status: number;
  constructor(status: number, code: string, message: string, details: Record<string, unknown> = {}) {
    super(message);
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

export async function api<T = any>(path: string, init: RequestInit & { json?: unknown } = {}): Promise<T> {
  const { json, ...rest } = init;
  const headers: Record<string, string> = { ...(rest.headers as Record<string, string>) };
  let body = rest.body;
  if (json !== undefined) {
    headers["Content-Type"] = "application/json";
    body = JSON.stringify(json);
  }
  let res: Response;
  try {
    res = await fetch(`${API_URL}/api/v1${path}`, { ...rest, headers, body, cache: "no-store" });
  } catch {
    throw new ApiError(0, "NETWORK", "Không kết nối được Core API (backend :8000)");
  }
  const data = res.status === 204 ? null : await res.json().catch(() => null);
  if (!res.ok) {
    const e = data?.error;
    throw new ApiError(res.status, e?.code || "HTTP_" + res.status, e?.message || res.statusText, e?.details || {});
  }
  return data as T;
}

export const fileUrl = (path: string) => `${API_URL}${path}`;

// ---------- types (subset of SRS v2 §7 contracts) ----------
export type Band = "HIGH" | "REVIEW" | "LOW" | null;
export type LineStatus = "NEEDS_CLARIFICATION" | "MATCHED" | "UNIT_CONVERTED" | "SUBSTITUTE_PROPOSED" | "CUSTOMER_ACCEPTED";

export interface Candidate {
  sku: string;
  name: string;
  score: number;
  band: Band;
  reasons: { matched: string[]; mismatched: string[]; missing: string[]; ambiguous?: boolean };
}

export interface Alternative {
  sku: string;
  name: string;
  on_hand: number;
  needed_quantity: number;
  selling_unit: string;
  formula: string;
  unit_price: number;
  currency: string;
  unit_price_delta: number;
  total_price_delta: number;
  different_grade: boolean;
  reasons: string[];
}

export interface Line {
  line_id: string;
  line_no: number;
  source: { text: string; start: number; end: number };
  parsed: { name: string | null; quantity: number | null; unit: string | null; unit_raw: string | null; status: string; warnings: string[] };
  match: { sku: string | null; name: string | null; match_score: number | null; band: Band; reasons: Candidate["reasons"] | Record<string, never>; candidates: Candidate[] };
  final_sku: string | null;
  final_name: string | null;
  unit_price: number | null;
  currency: string | null;
  chips: { attr: string; value: string; tone: "emerald" | "slate" | "red" }[];
  conversion: { requested: string; selling_quantity: number | null; selling_unit: string | null; formula: string | null; rounded: boolean; blocked_reason: string | null };
  line_status: LineStatus;
  stock: { status: "IN_STOCK" | "PARTIAL" | "OUT_OF_STOCK" | "UNKNOWN" | null; on_hand: number | null; updated_at: string | null; label: string };
  alternatives: Alternative[];
  fulfillment_action: string | null;
  resolved: boolean;
  associate_edited: boolean;
  substitution: { accepted_at: string | null; rejection_reason: string | null };
  requires_review: boolean;
}

export interface SessionView {
  session_id: string;
  order_session_id: string;
  status: string;
  input_type: "paste_text" | "email" | "file";
  market: string;
  store_id: string;
  user_id: string;
  client_id: string | null;
  masked_source: string | null;
  read_line_count: number;
  ai_degraded: boolean;
  analyzed: boolean;
  locked: boolean;
  stage_timings_ms: Record<string, number | boolean>;
  lines: Line[];
  blockers: { line_no: number; reason: string }[];
  quote: { quote_id: string; status: string } | null;
  confirmation: {
    order_status: string | null;
    fulfillment_reference: string | null;
    pos_order_ref: string | null;
    csv_download_url: string | null;
    confirmed_at: string | null;
    processing_time_seconds: number | null;
  };
}

export interface Customer {
  client_id: string;
  customer_type: "B2B" | "B2C_WalkIn";
  discount_tier: string;
}

export interface QuoteLine {
  line_no: number;
  raw_customer_input: string;
  sku: string;
  name: string;
  category: string;
  quantity: number;
  selling_unit: string;
  snapshot: { unit_price: number; list_unit_price: number; on_hand: number; line_total: number };
  live: { unit_price: number; on_hand: number | null; checked_at: string; stock_updated_at: string | null } | null;
  changed_fields: ("price" | "stock")[];
  alternative_required: boolean;
  current_line: { final_sku: string; line_status: LineStatus; stock_status: string | null; fulfillment_action: string | null } | null;
}

export interface QuoteView {
  quote_id: string;
  status: "SAVED" | "SENT" | "PREPARING" | "CONFIRMED" | "EXPIRED" | "CANCELLED";
  session_id: string;
  order_session_id: string;
  client_id: string;
  customer_type: string | null;
  valid_until: string;
  price_source: string;
  price_captured_at: string;
  applied_discount_tier: string;
  discount_rate: number;
  currency: string;
  customer_confirmed_at: string | null;
  customer_confirmed_by: string | null;
  created_at: string | null;
  created_by: string | null;
  status_changed_at: string | null;
  status_changed_by: string | null;
  disclaimer: string;
  snapshot_total: number;
  lines: QuoteLine[];
  live_checked_at: string | null;
  live_error: string | null;
  session_status: string;
  session_locked: boolean;
  order: { fulfillment_reference: string | null; pos_order_ref: string | null; csv_download_url: string | null };
  allowed_actions: string[];
  changes?: { line_no: number; changed_fields: string[]; alternative_required: boolean }[];
}

export interface Health {
  status: string;
  database: string;
  mock_pos: string;
  ai_fail_mode: boolean;
  pos_fail_mode: boolean;
}

export const fmtTime = (iso?: string | null) =>
  iso ? new Date(iso).toLocaleString("vi-VN", { hour: "2-digit", minute: "2-digit", day: "2-digit", month: "2-digit" }) : "—";

export const fmtMoney = (n?: number | null, cur = "DKK") =>
  n === null || n === undefined ? "—" : `${n.toLocaleString("da-DK", { minimumFractionDigits: 2, maximumFractionDigits: 2 })} ${cur}`;

export const UNIT_LABEL: Record<string, string> = {
  piece: "cái/cây",
  linear_metre: "m dài",
  square_metre: "m²",
  pack: "gói",
  bag: "bao",
  board: "tấm",
};
