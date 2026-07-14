import { ApiClient } from './client'
import type { Freshness, Opportunity } from './market-workspace'

export interface SymbolSearchItem {
  underlying_symbol: string
  latest_captured_at: string
  expiries: string[]
}
export interface Analytics {
  analytics_id: string
  source_run_id: string
  source_captured_at: string
  calculated_at: string
  spot_price: string
  atm_strike: string
  atm_straddle_cost: string
  total_call_oi: number
  total_put_oi: number
  total_pcr: string | null
  nearby_call_oi: number
  nearby_put_oi: number
  nearby_pcr: string | null
  atm_call_iv: string | null
  atm_put_iv: string | null
  atm_mean_iv: string | null
  nearby_mean_iv: string | null
  price_coverage: string
  liquidity_coverage: string
}
export interface Selection {
  selection_id: string
  ranking_id: string
  calculated_at: string
  trading_symbol: string
  option_type: string
  strike: string
  contract_score: string
  explanation: Record<string, unknown>
}
export interface Risk {
  assessment_id: string
  selection_id: string
  calculated_at: string
  approved: boolean
  approved_lots: number
  approved_quantity: number
  approved_exposure: string
  maximum_loss: string
  rejection_code: string | null
  explanation: Record<string, unknown>
}
export interface Signal {
  signal_id: string
  assessment_id: string
  calculated_at: string
  action: string
  direction: string
  confidence_score: string
  rationale: Record<string, unknown>
}
export interface TimelineEvent {
  type: string
  timestamp: string
  id: string
}
export interface SymbolIntelligence {
  symbol: string
  expiry: string
  freshness: Freshness
  last_update: string
  current_ranking: Opportunity | null
  previous_rank: number | null
  rank_movement: number | null
  analytics: Analytics[]
  changes: Array<Record<string, unknown>>
  rankings: Opportunity[]
  selections: Selection[]
  risk: Risk[]
  signals: Signal[]
  timeline: TimelineEvent[]
  related: Array<{
    ranking_id: string
    expiry: string
    rank_position: number
    total_score: string
    source_captured_at: string
  }>
  unsupported: string[]
}

const client = new ApiClient()
export const symbolWorkspaceApi = {
  search: (query: string, signal?: AbortSignal) =>
    client.get<{ data: SymbolSearchItem[]; count: number }>(
      `/api/v2/symbols?query=${encodeURIComponent(query)}&limit=10`,
      signal,
    ),
  intelligence: (symbol: string, expiry: string | undefined, signal?: AbortSignal) =>
    client.get<{ data: SymbolIntelligence }>(
      `/api/v2/symbols/${encodeURIComponent(symbol)}${expiry ? `?expiry=${encodeURIComponent(expiry)}` : ''}`,
      signal,
    ),
}
