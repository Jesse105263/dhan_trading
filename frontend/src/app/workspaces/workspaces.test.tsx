import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import {
  marketWorkspaceApi,
  type OpportunitiesResponse,
  type OverviewResponse,
} from '../../api/market-workspace'
import { MarketOverviewPage } from './MarketOverviewPage'
import { OpportunityDetailPage } from './OpportunityDetailPage'
import { OpportunityScannerPage } from './OpportunityScannerPage'

vi.mock('../../api/market-workspace', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../../api/market-workspace')>()
  return {
    ...actual,
    marketWorkspaceApi: { overview: vi.fn(), opportunities: vi.fn(), opportunity: vi.fn() },
  }
})

const item = {
  ranking_id: '11111111-1111-4111-8111-111111111111',
  ranking_run_id: 'run-1',
  analytics_id: 'analytics-1',
  change_id: 'change-1',
  underlying_symbol: 'RELIANCE',
  expiry: '2026-07-30',
  source_captured_at: '2026-07-14T11:55:00',
  rank_position: 1,
  total_score: '0.88',
  liquidity_score: '0.90',
  activity_score: '0.80',
  volatility_score: '0.70',
  directional_score: '0.60',
  explanation: { summary: 'strong persisted evidence' },
  freshness: 'stale' as const,
  selection_available: true,
  risk_approved: true,
  signal_available: false,
}
const overview: OverviewResponse = {
  platform: { status: 'ok', database_ready: true },
  freshness: { state: 'stale', source_timestamp: '2026-07-14T11:00:00' },
  latest_option_run: {
    run_id: 'option-run',
    underlying_symbol: 'RELIANCE',
    expiry: '2026-07-30',
    completed_at: '2026-07-14T11:00:00',
  },
  latest_ranking_run: {
    ranking_run_id: 'ranking-run',
    calculated_at: '2026-07-14T11:01:00',
    eligible_count: 1,
  },
  counts: { ranked: 1, selections: 1, risk_approved: 1, risk_rejected: 0, signals: 0 },
  recent_failures: [],
}
const opportunities: OpportunitiesResponse = {
  data: [item],
  page: { limit: 50, offset: 0, count: 1, total: 1 },
  sort: { field: 'rank', direction: 'asc' },
}

describe('market workspaces', () => {
  beforeEach(() => vi.clearAllMocks())

  it('renders overview metrics, lineage, empty failures and stale state', async () => {
    vi.mocked(marketWorkspaceApi.overview).mockResolvedValue(overview)
    render(
      <MemoryRouter>
        <MarketOverviewPage />
      </MemoryRouter>,
    )
    expect(screen.getByLabelText('Loading content')).toBeInTheDocument()
    expect(await screen.findByText('ranking-run')).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Market Overview' })).toBeInTheDocument()
    expect(screen.getByText('No recent failures')).toBeInTheDocument()
    expect(screen.getByText('stale')).toBeInTheDocument()
  })

  it('renders dense scanner and navigable detail action', async () => {
    vi.mocked(marketWorkspaceApi.opportunities).mockResolvedValue(opportunities)
    render(
      <MemoryRouter>
        <OpportunityScannerPage />
      </MemoryRouter>,
    )
    expect(await screen.findByRole('cell', { name: 'RELIANCE' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Inspect' })).toHaveAttribute(
      'href',
      `/opportunities/${item.ranking_id}`,
    )
    expect(screen.getByText('Approved')).toBeInTheDocument()
  })

  it('submits accessible filters and sorting controls', async () => {
    vi.mocked(marketWorkspaceApi.opportunities).mockResolvedValue(opportunities)
    render(
      <MemoryRouter>
        <OpportunityScannerPage />
      </MemoryRouter>,
    )
    await screen.findByRole('cell', { name: 'RELIANCE' })
    fireEvent.change(screen.getByLabelText('Symbol'), { target: { value: 'tcs' } })
    fireEvent.change(screen.getByLabelText('Risk approved'), { target: { value: 'true' } })
    fireEvent.click(screen.getByRole('button', { name: 'Apply' }))
    await waitFor(() =>
      expect(vi.mocked(marketWorkspaceApi.opportunities).mock.calls.at(-1)?.[0].get('symbol')).toBe(
        'TCS',
      ),
    )
    fireEvent.click(screen.getByRole('button', { name: 'Score' }))
    await waitFor(() =>
      expect(vi.mocked(marketWorkspaceApi.opportunities).mock.calls.at(-1)?.[0].get('sort')).toBe(
        'score',
      ),
    )
  })

  it('renders empty and API unavailable states', async () => {
    vi.mocked(marketWorkspaceApi.opportunities).mockResolvedValue({
      ...opportunities,
      data: [],
      page: { ...opportunities.page, count: 0, total: 0 },
    })
    const view = render(
      <MemoryRouter>
        <OpportunityScannerPage />
      </MemoryRouter>,
    )
    expect(await screen.findByText('No ranked opportunities')).toBeInTheDocument()
    view.unmount()
    vi.mocked(marketWorkspaceApi.overview).mockRejectedValue(new Error('database unavailable'))
    render(
      <MemoryRouter>
        <MarketOverviewPage />
      </MemoryRouter>,
    )
    expect(await screen.findByText('Market overview unavailable')).toBeInTheDocument()
  })

  it('renders detail lineage and not-found behavior', async () => {
    vi.mocked(marketWorkspaceApi.opportunity).mockResolvedValue({
      data: {
        ...item,
        selection_id: 'selection-1',
        assessment_id: 'assessment-1',
        approved: true,
        signal_id: null,
        trading_symbol: 'RELIANCE-CE',
      },
    })
    const view = render(
      <MemoryRouter initialEntries={[`/opportunities/${item.ranking_id}`]}>
        <Routes>
          <Route path="/opportunities/:rankingId" element={<OpportunityDetailPage />} />
        </Routes>
      </MemoryRouter>,
    )
    expect(await screen.findByText(/strong persisted evidence/u)).toBeInTheDocument()
    expect(screen.queryByText('selection-1')).not.toBeInTheDocument()
    view.unmount()
    vi.mocked(marketWorkspaceApi.opportunity).mockRejectedValue(new Error('404'))
    render(
      <MemoryRouter initialEntries={['/opportunities/missing']}>
        <Routes>
          <Route path="/opportunities/:rankingId" element={<OpportunityDetailPage />} />
        </Routes>
      </MemoryRouter>,
    )
    expect(await screen.findByText('Opportunity not found')).toBeInTheDocument()
  })
})
