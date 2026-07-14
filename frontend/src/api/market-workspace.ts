import { ApiClient } from './client'

export type Freshness = 'current' | 'aging' | 'stale' | 'unavailable'

export interface OverviewResponse {
  platform: { status: string; database_ready: boolean }
  freshness: { state: Freshness; source_timestamp: string | null }
  latest_option_run: {
    run_id: string
    underlying_symbol: string
    expiry: string
    completed_at: string
  } | null
  latest_ranking_run: {
    ranking_run_id: string
    calculated_at: string
    eligible_count: number
  } | null
  counts: {
    ranked: number
    selections: number
    risk_approved: number
    risk_rejected: number
    signals: number
  }
  recent_failures: Array<{
    id: number
    stage_name: string
    symbol: string | null
    error_type: string
    error_message: string
    occurred_at: string
  }>
}

export interface Opportunity {
  ranking_id: string
  ranking_run_id: string
  analytics_id: string
  change_id: string
  underlying_symbol: string
  expiry: string
  source_captured_at: string
  rank_position: number
  total_score: string
  liquidity_score: string
  activity_score: string
  volatility_score: string
  directional_score: string
  explanation: Record<string, unknown>
  freshness: Freshness
  selection_available: boolean
  risk_approved: boolean
  signal_available: boolean
  selection_id?: string | null
  assessment_id?: string | null
  approved?: boolean | null
  rejection_code?: string | null
  signal_id?: string | null
  trading_symbol?: string | null
}

export interface OpportunityResponse {
  data: Opportunity
}
export interface OpportunitiesResponse {
  data: Opportunity[]
  page: { limit: number; offset: number; count: number; total: number }
  sort: { field: string; direction: string }
}

const client = new ApiClient()

export const marketWorkspaceApi = {
  overview: (signal?: AbortSignal) => client.get<OverviewResponse>('/api/v2/overview', signal),
  opportunities: (parameters: URLSearchParams, signal?: AbortSignal) =>
    client.get<OpportunitiesResponse>(`/api/v2/opportunities?${parameters}`, signal),
  opportunity: (id: string, signal?: AbortSignal) =>
    client.get<OpportunityResponse>(`/api/v2/opportunities/${encodeURIComponent(id)}`, signal),
}
