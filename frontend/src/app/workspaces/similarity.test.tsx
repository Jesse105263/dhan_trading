import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { similarityApi } from '../../api/similarity'
import { SimilarityPage } from './SimilarityPage'

vi.mock('../../api/similarity', () => ({ similarityApi: { vectors: vi.fn(), analyze: vi.fn() } }))
const vector = {
  vector_id: '11111111-1111-4111-8111-111111111111',
  underlying_symbol: 'ABC',
  expiry: '2026-08-27',
  observed_at: '2026-07-14T10:00:00',
}

describe('SimilarityPage', () => {
  beforeEach(() => vi.clearAllMocks())
  it('selects a vector and renders ranked evidence with an insufficient warning', async () => {
    vi.mocked(similarityApi.vectors).mockResolvedValue({ data: [vector] })
    vi.mocked(similarityApi.analyze).mockResolvedValue({
      data: {
        run_id: 'run',
        model_version: 'option-observation-similarity-v1',
        evidence_state: 'INSUFFICIENT',
        candidate_count: 1,
        match_count: 1,
        statistics: {
          usable_outcome_count: 1,
          classified_count: 1,
          historical_win_rate: 1,
          average_closing_return: 2,
          average_mfe: 3,
          average_mae: -1,
        },
        matches: [
          {
            ...vector,
            analytics_id: 'analytics',
            ranking_id: null,
            rank: 1,
            distance: 0,
            similarity_score: 1,
            shared_feature_count: 8,
            missing_feature_count: 4,
            outcome: {
              outcome_id: 'outcome',
              outcome_type: 'EXPIRY_COMPLETE',
              closing_return: 2,
              maximum_favourable_excursion: 3,
              maximum_adverse_excursion: -1,
              won: true,
            },
          },
        ],
      },
    })
    render(
      <MemoryRouter>
        <SimilarityPage />
      </MemoryRouter>,
    )
    fireEvent.change(screen.getByLabelText('Symbol'), { target: { value: 'abc' } })
    fireEvent.click(screen.getByRole('button', { name: 'Find observations' }))
    await screen.findByRole('button', { name: /2026.*2026-08-27/ })
    fireEvent.click(screen.getByRole('button', { name: /2026.*2026-08-27/ }))
    expect(await screen.findByText('Ranked historical matches')).toBeInTheDocument()
    expect(screen.getByRole('alert')).toHaveTextContent('Too few classified')
    expect(screen.getByRole('link', { name: 'Vector' })).toHaveAttribute(
      'href',
      `/api/v2/features/${vector.vector_id}`,
    )
  })
  it('renders API errors accessibly', async () => {
    vi.mocked(similarityApi.vectors).mockRejectedValue(new Error('offline'))
    render(
      <MemoryRouter>
        <SimilarityPage />
      </MemoryRouter>,
    )
    fireEvent.change(screen.getByLabelText('Symbol'), { target: { value: 'ABC' } })
    fireEvent.click(screen.getByRole('button', { name: 'Find observations' }))
    await waitFor(() =>
      expect(screen.getByText('Similarity evidence unavailable')).toBeInTheDocument(),
    )
  })
})
