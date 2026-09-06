/**
 * Minimal TypeScript client for the Vibe-Trading advisor API.
 *
 * Drop this file into your finance app. It has no dependencies beyond `fetch`.
 * Point `baseUrl` at the locally running server (default http://127.0.0.1:8899)
 * and pass the same value you set as API_AUTH_KEY in agent/.env.
 */

export type AccountType = "taxable" | "roth_ira" | "traditional_ira" | "401k" | "hsa" | "crypto" | "other";
export type AssetClass = "stock" | "etf" | "crypto" | "bond" | "cash" | "other";
export type Action = "buy" | "sell" | "trim" | "hold";
export type RecStatus = "open" | "accepted" | "rejected" | "expired";

export interface PositionIn { symbol: string; quantity: number; cost_basis_usd?: number; asset_class?: AssetClass }
export interface AccountIn { id: string; name: string; type: AccountType; cash_usd: number; positions: PositionIn[] }
export interface HoldingsIn { accounts: AccountIn[]; source?: string; as_of?: string }

export interface Objectives {
  risk_tolerance?: "conservative" | "moderate" | "aggressive";
  horizon_years?: number;
  single_stock_sleeve_cap?: number;   // 0.4 = individual stocks capped at 40% of total
  max_position_weight?: number;       // 0.15 = no single position above 15%
  benchmark?: string;                 // default SPY
  notes?: string;                     // free text the advisor reads as part of the mandate
}

export interface Recommendation {
  id: string; created_at: string; status: RecStatus; decided_at: string | null; note: string | null;
  action: Action; symbol: string; is_new_position: boolean;
  account_id: string | null; resolved_account_id: string | null;
  amount_usd: number | null; target_weight: number | null; quantity: number | null;
  price_at_rec: number | null; priced: boolean;
  rationale: string; confidence: number; horizon: "weeks" | "months" | "years"; tax_note: string;
}

export interface Review {
  id: string; created_at: string; snapshot_id: string; model: string | null;
  prices_as_of: string | null; total_value_usd: number | null;
  summary: string; allocation_findings: string[]; risk_findings: string[]; tax_findings: string[];
  watchlist: string[]; data_gaps: string[];
  allocation: Record<string, unknown>; risk: Record<string, unknown>; benchmark: Record<string, unknown> | null;
  recommendations: Recommendation[];
}

export interface ScoredRecommendation extends Pick<Recommendation, "id" | "symbol" | "action" | "status" | "price_at_rec" | "amount_usd" | "confidence"> {
  price_now: number | null; symbol_return: number | null; benchmark_return: number | null; excess: number | null; hit: boolean | null;
}

export interface ReviewPerformance {
  review_id: string; since: string; as_of?: string; status: "ok" | "no_data"; benchmark?: string;
  benchmark_return?: number | null; actual_value_start?: number; actual_value_now?: number;
  hypothetical_value_now?: number; advice_delta_usd?: number; actual_return?: number | null; hypothetical_return?: number | null;
  curve?: { date: string; actual: number; hypothetical: number; benchmark: number | null }[];
  recommendations?: ScoredRecommendation[]; data_gaps: string[];
}

export interface Scorecard {
  reviews: number; scored_recommendations: number; hit_rate: number | null; avg_excess_return: number | null;
  by_action: Record<string, { n: number; hit_rate: number; avg_excess_return: number }>; advice_delta_usd_total: number;
}

export class AdvisorClient {
  constructor(private baseUrl = "http://127.0.0.1:8899", private apiKey?: string) {}

  private async call<T>(path: string, init: RequestInit = {}): Promise<T> {
    const headers: Record<string, string> = { "Content-Type": "application/json", ...(init.headers as Record<string, string>) };
    if (this.apiKey) headers.Authorization = `Bearer ${this.apiKey}`;
    const res = await fetch(`${this.baseUrl}${path}`, { ...init, headers });
    if (!res.ok) throw new Error(`advisor ${path} -> ${res.status}: ${await res.text()}`);
    return (await res.json()) as T;
  }

  /** Push the latest balances from your aggregator. Returns a valued snapshot. */
  pushHoldings(holdings: HoldingsIn) {
    return this.call<{ snapshot_id: string; total_value_usd: number; accounts: unknown[]; holdings: unknown[]; allocation: unknown; data_gaps: string[] }>(
      "/advisor/holdings", { method: "POST", body: JSON.stringify(holdings) });
  }

  /** Run a wealth-manager review of the latest snapshot. Takes 30-120 s (one LLM call). */
  async review(objectives: Objectives = {}, snapshotId?: string): Promise<Review> {
    const r = await this.call<{ review: Review }>("/advisor/review", { method: "POST", body: JSON.stringify({ snapshot_id: snapshotId ?? null, objectives }) });
    return r.review;
  }

  async listReviews(limit = 20) { return (await this.call<{ reviews: Omit<Review, "recommendations">[] }>(`/advisor/reviews?limit=${limit}`)).reviews; }
  async getReview(id: string) { return (await this.call<{ review: Review }>(`/advisor/reviews/${id}`)).review; }

  async listRecommendations(status?: RecStatus, reviewId?: string) {
    const q = new URLSearchParams(); if (status) q.set("status", status); if (reviewId) q.set("review_id", reviewId);
    return (await this.call<{ recommendations: Recommendation[] }>(`/advisor/recommendations?${q}`)).recommendations;
  }

  /** Record what you actually did with a recommendation. */
  async decide(recId: string, status: "accepted" | "rejected", note = "") {
    return (await this.call<{ recommendation: Recommendation }>(`/advisor/recommendations/${recId}/decision`, { method: "POST", body: JSON.stringify({ status, note }) })).recommendation;
  }

  /** Track record: every review's frozen book vs the advised book vs SPY, plus per-call scoring. */
  performance(reviewId?: string) {
    return this.call<{ scorecard: Scorecard; reviews: ReviewPerformance[] }>(`/advisor/performance${reviewId ? `?review_id=${reviewId}` : ""}`);
  }
}
