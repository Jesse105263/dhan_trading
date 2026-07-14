import { ApiClient } from './client'

const apiClient = new ApiClient({ baseUrl: import.meta.env.VITE_API_BASE_URL })

export interface FeatureVector {
  vector_id: string
  underlying_symbol: string
  expiry: string
  observed_at: string
}
export interface SimilarityMatch extends FeatureVector {
  analytics_id: string
  ranking_id: string | null
  rank: number
  distance: number
  similarity_score: number
  shared_feature_count: number
  missing_feature_count: number
  outcome: null | {
    outcome_id: string
    outcome_type: string
    closing_return: number | null
    maximum_favourable_excursion: number | null
    maximum_adverse_excursion: number | null
    won: boolean | null
  }
}
export interface SimilarityResult {
  run_id: string
  model_version: string
  evidence_state: 'SUFFICIENT' | 'INSUFFICIENT'
  candidate_count: number
  match_count: number
  matches: SimilarityMatch[]
  statistics: {
    usable_outcome_count: number
    classified_count: number
    historical_win_rate: number | null
    average_closing_return: number | null
    average_mfe: number | null
    average_mae: number | null
  }
}

export const similarityApi = {
  vectors: (symbol: string, signal?: AbortSignal) =>
    apiClient.get<{ data: FeatureVector[] }>(
      `/api/v2/features?symbol=${encodeURIComponent(symbol)}&limit=100`,
      signal,
    ),
  analyze: (vectorId: string, signal?: AbortSignal) =>
    apiClient.get<{ data: SimilarityResult }>(
      `/api/v2/similarity?vector_id=${encodeURIComponent(vectorId)}&limit=20`,
      signal,
    ),
}
