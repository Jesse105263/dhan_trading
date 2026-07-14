import { fireEvent, render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { newsEventApi, type MarketEvent } from '../../api/news-events'
import { NewsEventPage } from './NewsEventPage'

vi.mock('../../api/news-events', () => ({ newsEventApi: { list: vi.fn(), opportunity: vi.fn() } }))
const event: MarketEvent = {
  event_id: '11111111-1111-4111-8111-111111111111',
  source: 'fixture',
  source_event_id: 'event-1',
  event_type: 'RBI',
  title: 'RBI policy event',
  summary: 'Persisted local fixture',
  published_at: '2026-07-10T10:00:00',
  event_at: '2026-07-17T10:00:00',
  is_scheduled: true,
  market_wide: true,
  source_reference: 'fixture:event-1',
  symbols: [],
  sectors: [],
  raw_source_checksum: 'a'.repeat(64),
}

describe('NewsEventPage', () => {
  beforeEach(() => vi.clearAllMocks())
  it('renders source-attributed scheduled timeline and symbol filters', async () => {
    vi.mocked(newsEventApi.list).mockResolvedValue({ data: [event], count: 1, limit: 100 })
    render(
      <MemoryRouter>
        <NewsEventPage />
      </MemoryRouter>,
    )
    expect(await screen.findByRole('heading', { name: 'RBI policy event' })).toBeInTheDocument()
    expect(screen.getByText('fixture:event-1')).toBeInTheDocument()
    expect(screen.getByText('SCHEDULED')).toBeInTheDocument()
    fireEvent.change(screen.getByLabelText('Symbol'), { target: { value: 'RELIANCE' } })
    fireEvent.click(screen.getByRole('button', { name: 'Apply filters' }))
    expect(newsEventApi.list).toHaveBeenCalled()
  })
  it('renders empty and error states', async () => {
    vi.mocked(newsEventApi.list).mockResolvedValueOnce({ data: [], count: 0, limit: 100 })
    const { unmount } = render(
      <MemoryRouter>
        <NewsEventPage />
      </MemoryRouter>,
    )
    expect(await screen.findByText('No persisted event context')).toBeInTheDocument()
    unmount()
    vi.mocked(newsEventApi.list).mockRejectedValueOnce(new Error('offline'))
    render(
      <MemoryRouter>
        <NewsEventPage />
      </MemoryRouter>,
    )
    expect(await screen.findByText('Event intelligence unavailable')).toBeInTheDocument()
  })
})
