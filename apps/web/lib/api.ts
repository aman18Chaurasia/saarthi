const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface AnalyticsSummary {
  total_calls: number;
  qualified_count: number;
  qualified_rate: number;
  avg_duration_s: number;
  avg_turn_count: number;
  p50_latency: number;
  p95_latency: number;
  high_priority_calls: number;
  follow_up_queue: number;
  handoff_queue: number;
  avg_lead_score: number;
  negative_sentiment_rate: number;
  top_objections: Array<{ objection: string; count: number }>;
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
  slots_redacted: Record<string, unknown>;
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
  avg_lead_score: number;
  follow_up_queue: number;
}

export interface CallIntelligence {
  lead_score: number;
  priority: "high" | "medium" | "low";
  sentiment: "positive" | "neutral" | "negative";
  objections: string[];
  needs_follow_up: boolean;
  recommended_callback_window: string | null;
  handoff_recommended: boolean;
  follow_up_action: string;
  summary: string;
}

export interface CallDetail extends CallRow {
  transcript_redacted: Array<{
    speaker: string;
    text: string;
    node: string;
    turn_index: number;
  }>;
  latency_stats: Record<string, number>;
  intelligence: CallIntelligence;
}

export interface OpsSummary {
  high_priority_calls: number;
  follow_up_queue: number;
  handoff_queue: number;
  avg_lead_score: number;
  negative_sentiment_rate: number;
  top_objections: Array<{ objection: string; count: number }>;
}

export interface FollowUpTask {
  task_id: string;
  call_id: string;
  channel: string;
  scheduled_for: string;
  message: string;
  status: string;
  recipient?: string | null;
  provider?: string | null;
  external_id?: string | null;
  detail?: string | null;
}

export interface FollowUpsResponse {
  tasks: FollowUpTask[];
}

export interface SupervisorLiveResponse {
  active_calls: Array<{
    call_id: string;
    product: string;
    started_at: string;
    agent_name: string;
    customer_name_redacted: string;
    transcript_preview: Array<{ speaker: string; text: string; node: string; turn_index: number }>;
    compliance_flags: string[];
  }>;
  watchlist: Array<{
    call_id: string;
    product: string;
    outcome: string | null;
    started_at: string;
    lead_score: number;
    handoff_recommended: boolean;
    compliance_flags: string[];
  }>;
}

export interface EvalLabResponse {
  total_personas: number;
  products: Array<{ product: string; personas: number }>;
  baseline_accuracy: number;
  improved_accuracy: number;
  win_rate_gain: number;
  failure_clusters: Array<{ cluster: string; count: number }>;
}

export interface RecommendationResponse {
  recommended_product: string;
  secondary_product: string;
  confidence: number;
  reason: string;
  routing_target: string;
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
