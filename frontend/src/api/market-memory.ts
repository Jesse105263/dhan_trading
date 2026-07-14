import { ApiClient } from './client'

const apiClient = new ApiClient({ baseUrl: import.meta.env.VITE_API_BASE_URL })

export type FeatureValue = string | number | null
export interface MemorySnapshot {
  snapshot_id: string
  snapshot_type: 'option_analytics'
  symbol: string
  expiry: string
  captured_at: string
  calculated_at: string
  freshness: 'current' | 'aging' | 'stale' | 'unavailable'
  features: Record<string, FeatureValue>
  lineage: Record<string, string | null>
}
export interface MemoryList {
  data: MemorySnapshot[]
  count: number
  limit: number
  features: string[]
}
export interface MemoryComparison {
  symbol: string
  expiry: string
  previous_snapshot_id: string
  current_snapshot_id: string
  previous_captured_at: string
  current_captured_at: string
  changes: Array<{ feature: string; previous: FeatureValue; current: FeatureValue }>
}

export const marketMemoryApi = {
  list: (parameters: URLSearchParams, signal?: AbortSignal) =>
    apiClient.get<MemoryList>(`/api/v2/memory?${parameters}`, signal),
  compare: (previous: string, current: string, signal?: AbortSignal) =>
    apiClient.get<{ data: MemoryComparison }>(
      `/api/v2/memory/compare?previous=${encodeURIComponent(previous)}&current=${encodeURIComponent(current)}`,
      signal,
    ),
}
