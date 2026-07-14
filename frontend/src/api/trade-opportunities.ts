import { ApiClient } from './client'

const apiClient = new ApiClient({ baseUrl: import.meta.env.VITE_API_BASE_URL })

export type OpportunityState = 'ELIGIBLE' | 'INSUFFICIENT_EVIDENCE' | 'NO_OPPORTUNITY'
export interface TradeOpportunity {
  opportunity_id: string
  similarity_run_id: string
  query_vector_id: string
  query_analytics_id: string
  query_ranking_id: string | null
  underlying_symbol: string
  expiry: string
  observed_at: string
  model_version: string
  state: OpportunityState
  direction: 'LONG' | null
  rank_position: number
  opportunity_score: number | null
  evidence_quality: number
  match_count: number
  classified_count: number
  entry_zone_low: number | null
  entry_zone_high: number | null
  stop_zone: number | null
  target_zones: number[]
  expected_value: number | null
  historical_win_rate: number | null
  risk_reward: number | null
  reasons_for: string[]
  reasons_against: string[]
  evidence?: Array<{
    similarity_match_id: string
    matched_vector_id: string
    matched_outcome_id: string
    similarity_score: number
    shared_feature_count: number
    underlying_symbol: string
    expiry: string
    observed_at: string
  }>
}

export const tradeOpportunityApi = {
  list: (parameters: URLSearchParams, signal?: AbortSignal) =>
    apiClient.get<{ data: TradeOpportunity[]; count: number; limit: number }>(
      `/api/v2/trade-opportunities?${parameters}`,
      signal,
    ),
  detail: (identifier: string, signal?: AbortSignal) =>
    apiClient.get<{ data: TradeOpportunity }>(
      `/api/v2/trade-opportunities/${encodeURIComponent(identifier)}`,
      signal,
    ),
}
