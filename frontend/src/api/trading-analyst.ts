import { ApiClient } from './client'

const apiClient = new ApiClient({ baseUrl: import.meta.env.VITE_API_BASE_URL })

export interface AnalystCitation {
  id: string
  type: string
  citation: string
}

export interface AnalystResponse {
  status: 'ANSWERED' | 'REFUSED'
  provider: string
  answer: string
  citations: AnalystCitation[]
  evidence: Array<{
    opportunity_id: string
    evidence_state: string
    limitations: string[]
  }>
  model_error: string | null
}

export const tradingAnalystApi = {
  explain: (opportunityId: string, question: string, signal?: AbortSignal) =>
    apiClient.post<{ data: AnalystResponse }>(
      `/api/v2/analyst/opportunities/${encodeURIComponent(opportunityId)}/explain`,
      { question },
      signal,
    ),
  compare: (opportunityIds: string[], question: string, signal?: AbortSignal) =>
    apiClient.post<{ data: AnalystResponse }>(
      '/api/v2/analyst/compare',
      { question, opportunity_ids: opportunityIds },
      signal,
    ),
}
