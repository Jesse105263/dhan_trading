import { ApiClient } from './client'

const apiClient = new ApiClient({ baseUrl: import.meta.env.VITE_API_BASE_URL })

export interface MarketEvent {
  event_id: string
  source: string
  source_event_id: string
  event_type: string
  title: string
  summary: string
  published_at: string | null
  event_at: string | null
  is_scheduled: boolean
  market_wide: boolean
  source_reference: string | null
  symbols: string[]
  sectors: string[]
  raw_source_checksum: string
}
export interface OpportunityEventContext {
  opportunity_id: string
  events: Array<{
    event_id: string
    context_type: 'RECENT_CONTEXT' | 'UPCOMING_RISK'
    seconds_from_observation: number
    event: MarketEvent
    symbols: string[]
  }>
  recent_event_count: number
  upcoming_event_count: number
  reasons_for: string[]
  reasons_against: string[]
  limitations: string[]
}

export const newsEventApi = {
  list: (parameters: URLSearchParams, signal?: AbortSignal) =>
    apiClient.get<{ data: MarketEvent[]; count: number; limit: number }>(
      `/api/v2/events?${parameters}`,
      signal,
    ),
  opportunity: (identifier: string, signal?: AbortSignal) =>
    apiClient.get<{ data: OpportunityEventContext }>(
      `/api/v2/trade-opportunities/${encodeURIComponent(identifier)}/events`,
      signal,
    ),
}
