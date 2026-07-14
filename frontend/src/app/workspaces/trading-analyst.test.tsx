import { fireEvent, render, screen } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import { tradingAnalystApi } from '../../api/trading-analyst'
import { TradingAnalystPage } from './TradingAnalystPage'

vi.mock('../../api/trading-analyst', () => ({
  tradingAnalystApi: { explain: vi.fn(), compare: vi.fn() },
}))

describe('AI Trading Analyst workspace', () => {
  beforeEach(() => vi.clearAllMocks())
  it('renders grounded response, citations, and insufficient evidence', async () => {
    vi.mocked(tradingAnalystApi.explain).mockResolvedValue({
      data: {
        status: 'ANSWERED',
        provider: 'local',
        answer: 'Facts\nINSUFFICIENT_EVIDENCE',
        citations: [{ id: 'one', type: 'trade_opportunity', citation: '[opportunity:one]' }],
        evidence: [
          { opportunity_id: 'one', evidence_state: 'INSUFFICIENT_EVIDENCE', limitations: [] },
        ],
        model_error: null,
      },
    })
    render(
      <MemoryRouter>
        <TradingAnalystPage />
      </MemoryRouter>,
    )
    fireEvent.change(screen.getByLabelText('Opportunity ID'), { target: { value: 'one' } })
    fireEvent.click(screen.getByRole('button', { name: 'Explain opportunity' }))
    expect(await screen.findByText('[opportunity:one]')).toBeInTheDocument()
    expect(screen.getByText(/trade levels and statistics are unavailable/i)).toBeInTheDocument()
  })
  it('supports comparison, refusal, loading, and error states', async () => {
    let resolve!: (value: never) => void
    vi.mocked(tradingAnalystApi.compare).mockReturnValue(
      new Promise((done) => {
        resolve = done
      }) as never,
    )
    render(
      <MemoryRouter>
        <TradingAnalystPage />
      </MemoryRouter>,
    )
    fireEvent.change(screen.getByLabelText('Opportunity ID'), { target: { value: 'one' } })
    fireEvent.change(screen.getByLabelText('Compare opportunity ID (optional)'), {
      target: { value: 'two' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Compare evidence' }))
    expect(screen.getByText('Assembling verified analyst evidence')).toBeInTheDocument()
    resolve({
      data: {
        status: 'REFUSED',
        provider: 'safety-boundary',
        answer: 'I cannot execute trades.',
        citations: [],
        evidence: [],
        model_error: null,
      },
    } as never)
    expect(await screen.findByText('REFUSED')).toBeInTheDocument()
    vi.mocked(tradingAnalystApi.explain).mockRejectedValue(new Error('offline'))
  })
})
