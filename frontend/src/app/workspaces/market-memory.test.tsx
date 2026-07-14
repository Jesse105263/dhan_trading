import { fireEvent, render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { marketMemoryApi, type MemoryList } from '../../api/market-memory'
import { MarketMemoryPage } from './MarketMemoryPage'

vi.mock('../../api/market-memory', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../../api/market-memory')>()
  return { ...actual, marketMemoryApi: { list: vi.fn(), compare: vi.fn() } }
})

const snapshots: MemoryList = {
  count: 2,
  limit: 50,
  features: ['atm_mean_iv', 'spot_price', 'total_score'],
  data: [
    {
      snapshot_id: '22222222-2222-4222-8222-222222222222',
      snapshot_type: 'option_analytics',
      symbol: 'RELIANCE',
      expiry: '2026-07-30',
      captured_at: '2026-07-14T12:00:00',
      calculated_at: '2026-07-14T12:01:00',
      freshness: 'current',
      features: { atm_mean_iv: '19', spot_price: '102', total_score: '0.8' },
      lineage: { source_run_id: 'run-2' },
    },
    {
      snapshot_id: '11111111-1111-4111-8111-111111111111',
      snapshot_type: 'option_analytics',
      symbol: 'RELIANCE',
      expiry: '2026-07-30',
      captured_at: '2026-07-14T11:00:00',
      calculated_at: '2026-07-14T11:01:00',
      freshness: 'stale',
      features: { atm_mean_iv: '17', spot_price: '100', total_score: '0.6' },
      lineage: { source_run_id: 'run-1' },
    },
  ],
}

describe('Market Memory workspace', () => {
  beforeEach(() => vi.clearAllMocks())
  it('renders evolution, stale state, and accessible comparison', async () => {
    vi.mocked(marketMemoryApi.list).mockResolvedValue(snapshots)
    vi.mocked(marketMemoryApi.compare).mockResolvedValue({
      data: {
        symbol: 'RELIANCE',
        expiry: '2026-07-30',
        previous_snapshot_id: snapshots.data[1]!.snapshot_id,
        current_snapshot_id: snapshots.data[0]!.snapshot_id,
        previous_captured_at: snapshots.data[1]!.captured_at,
        current_captured_at: snapshots.data[0]!.captured_at,
        changes: [{ feature: 'spot_price', previous: '100', current: '102' }],
      },
    })
    render(
      <MemoryRouter initialEntries={['/memory?symbol=RELIANCE']}>
        <MarketMemoryPage />
      </MemoryRouter>,
    )
    expect(await screen.findByRole('heading', { name: /Market Memory/u })).toBeInTheDocument()
    expect(screen.getByRole('img', { name: 'atm_mean_iv evolution' })).toBeInTheDocument()
    expect(screen.getByText('stale')).toBeInTheDocument()
    const boxes = screen.getAllByRole('checkbox', { name: /Compare snapshot/u })
    fireEvent.click(boxes[0]!)
    fireEvent.click(boxes[1]!)
    expect(await screen.findByText('spot_price')).toBeInTheDocument()
  })
  it('renders loading, empty and error states', async () => {
    vi.mocked(marketMemoryApi.list).mockResolvedValue({ ...snapshots, data: [], count: 0 })
    const view = render(
      <MemoryRouter initialEntries={['/memory?symbol=NONE']}>
        <MarketMemoryPage />
      </MemoryRouter>,
    )
    expect(screen.getByLabelText('Loading market memory')).toBeInTheDocument()
    expect(await screen.findByText('No snapshots')).toBeInTheDocument()
    view.unmount()
    vi.mocked(marketMemoryApi.list).mockRejectedValue(new Error('offline'))
    render(
      <MemoryRouter initialEntries={['/memory?symbol=NONE']}>
        <MarketMemoryPage />
      </MemoryRouter>,
    )
    expect(await screen.findByText('Market Memory unavailable')).toBeInTheDocument()
  })
})
