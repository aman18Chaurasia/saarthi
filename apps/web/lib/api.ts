const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface AnalyticsSummary {
  total_calls: number;
  qualified_count: number;
  qualified_rate: number;
  avg_duration_s: number;
  avg_turn_count: number;
  p50_latency: number;
  p95_latency: number;
}

export interface CallRow {
  call_id: string;
  customer_id: string;
  product: string;
  agent_name: string;
  lender_name: string;
  customer_name_redacted: string;
  status: string;
  outcome: string | null;
  started_at: string;
  ended_at: string | null;
  duration_s: number | null;
  turn_count: number;
  error_count: number;
  audio_failed: boolean;
}

export interface CallsResponse {
  calls: CallRow[];
  total: number;
  limit: number;
  offset: number;
}

export interface ProductAnalytics {
  product: string;
  call_count: number;
  qualified_rate: number;
  avg_duration: number;
}

export function apiUrl(path: string) {
  return `${API_BASE_URL}${path}`;
}

export async function fetchJson<T>(path: string): Promise<T> {
  const response = await fetch(apiUrl(path));
  if (!response.ok) {
    throw new Error(`API ${response.status}: ${response.statusText}`);
  }
  return response.json() as Promise<T>;
}

export function productLabel(product: string) {
  return product
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}
