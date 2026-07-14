import { fireEvent, render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { tradeOpportunityApi, type TradeOpportunity } from '../../api/trade-opportunities'
import { newsEventApi } from '../../api/news-events'
import { TradeOpportunityDetailPage } from './TradeOpportunityDetailPage'
import { TradeOpportunityPage } from './TradeOpportunityPage'

vi.mock('../../api/trade-opportunities', () => ({
  tradeOpportunityApi: { list: vi.fn(), detail: vi.fn() },
}))
vi.mock('../../api/news-events', () => ({
  newsEventApi: { list: vi.fn(), opportunity: vi.fn() },
}))
const item: TradeOpportunity = {
  opportunity_id: '11111111-1111-4111-8111-111111111111',
  similarity_run_id: 'run',
  query_vector_id: 'vector',
  query_analytics_id: 'analytics',
  query_ranking_id: null,
  underlying_symbol: 'ABC',
  expiry: '2026-08-27',
  observed_at: '2026-07-15T12:00:00',
  model_version: 'historical-long-opportunity-v1',
  state: 'ELIGIBLE',
  direction: 'LONG',
  rank_position: 1,
  opportunity_score: 75,
  evidence_quality: 0.8,
  match_count: 8,
  classified_count: 5,
  entry_zone_low: 96,
  entry_zone_high: 100,
  stop_zone: 95,
  target_zones: [106, 108],
  expected_value: 3,
  historical_win_rate: 0.8,
  risk_reward: 2.5,
  reasons_for: ['Positive evidence'],
  reasons_against: ['No guarantee'],
  evidence: [
    {
      similarity_match_id: 'match',
      matched_vector_id: 'matched-vector',
      matched_outcome_id: 'outcome',
      similarity_score: 0.9,
      shared_feature_count: 10,
      underlying_symbol: 'ABC',
      expiry: '2026-08-27',
      observed_at: '2026-06-01T12:00:00',
    },
  ],
}

describe('trade opportunity workspace', () => {
  beforeEach(() => vi.clearAllMocks())
  it('renders ranked levels and filters', async () => {
    vi.mocked(tradeOpportunityApi.list).mockResolvedValue({ data: [item], count: 1, limit: 50 })
    render(
      <MemoryRouter>
        <TradeOpportunityPage />
      </MemoryRouter>,
    )
    expect(await screen.findByText('96.00–100.00')).toBeInTheDocument()
    expect(screen.getByRole('option', { name: 'Insufficient evidence' })).toBeInTheDocument()
    fireEvent.change(screen.getByLabelText('Symbol'), { target: { value: 'abc' } })
    fireEvent.click(screen.getByRole('button', { name: 'Apply filters' }))
    expect(tradeOpportunityApi.list).toHaveBeenCalled()
  })
  it('renders detail, warnings, and exact lineage accessibly', async () => {
    vi.mocked(tradeOpportunityApi.detail).mockResolvedValue({ data: item })
    vi.mocked(newsEventApi.opportunity).mockResolvedValue({
      data: {
        opportunity_id: item.opportunity_id,
        events: [],
        recent_event_count: 0,
        upcoming_event_count: 0,
        reasons_for: [],
        reasons_against: [],
        limitations: [],
      },
    })
    render(
      <MemoryRouter initialEntries={[`/trade-opportunities/${item.opportunity_id}`]}>
        <Routes>
          <Route
            path="/trade-opportunities/:opportunityId"
            element={<TradeOpportunityDetailPage />}
          />
        </Routes>
      </MemoryRouter>,
    )
    expect(await screen.findByText('Evidence-derived levels')).toBeInTheDocument()
    expect(screen.getByText('No guarantee')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'vector' })).toHaveAttribute(
      'href',
      '/api/v2/features/matched-vector',
    )
  })
  it('shows an explicit read error', async () => {
    vi.mocked(tradeOpportunityApi.list).mockRejectedValue(new Error('offline'))
    render(
      <MemoryRouter>
        <TradeOpportunityPage />
      </MemoryRouter>,
    )
    expect(await screen.findByText('Opportunity evidence unavailable')).toBeInTheDocument()
  })
})
