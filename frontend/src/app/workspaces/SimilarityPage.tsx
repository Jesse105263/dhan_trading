import { useState } from 'react'
import { Link } from 'react-router-dom'
import { similarityApi, type FeatureVector, type SimilarityResult } from '../../api/similarity'
import {
  EmptyState,
  ErrorState,
  Input,
  PageHeader,
  Panel,
  SectionHeader,
  Skeleton,
  StatusPill,
} from '../../design-system'
import './similarity.css'

const percent = (value: number | null) =>
  value == null ? 'Unavailable' : `${(Number(value) * 100).toFixed(1)}%`

export function SimilarityPage() {
  const [symbol, setSymbol] = useState('')
  const [vectors, setVectors] = useState<FeatureVector[]>([])
  const [result, setResult] = useState<SimilarityResult>()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(false)
  async function loadVectors(event: React.FormEvent) {
    event.preventDefault()
    setLoading(true)
    setError(false)
    setResult(undefined)
    try {
      setVectors((await similarityApi.vectors(symbol.trim().toUpperCase())).data)
    } catch {
      setError(true)
    } finally {
      setLoading(false)
    }
  }
  async function analyze(vectorId: string) {
    setLoading(true)
    setError(false)
    try {
      setResult((await similarityApi.analyze(vectorId)).data)
    } catch {
      setError(true)
    } finally {
      setLoading(false)
    }
  }
  return (
    <div className="section-stack">
      <PageHeader
        eyebrow="Historical analogues"
        title="Similarity Engine"
        description="Compare a persisted Feature Store observation with earlier market situations. This is evidence, not a trade recommendation."
      />
      <Panel>
        <form
          className="similarity-controls"
          onSubmit={(event) => {
            void loadVectors(event)
          }}
        >
          <Input
            label="Symbol"
            value={symbol}
            onChange={(event) => setSymbol(event.target.value.toUpperCase())}
            required
          />
          <button className="ds-button ds-button--primary ds-button--md">Find observations</button>
        </form>
      </Panel>
      {loading && <Skeleton label="Loading historical similarity evidence" lines={8} />}
      {error && (
        <ErrorState
          title="Similarity evidence unavailable"
          description="The persisted evidence could not be read."
        />
      )}
      {!loading && !error && vectors.length > 0 && !result && (
        <Panel>
          <SectionHeader
            title="Choose a Feature Store observation"
            description="Only observations at or before its timestamp can be matched."
          />
          <div className="similarity-vector-list">
            {vectors.map((vector) => (
              <button
                key={vector.vector_id}
                className="ds-button ds-button--secondary ds-button--md"
                onClick={() => void analyze(vector.vector_id)}
              >
                {new Date(vector.observed_at).toLocaleString()} · {vector.expiry}
              </button>
            ))}
          </div>
        </Panel>
      )}
      {!loading && !error && symbol && !vectors.length && (
        <EmptyState
          title="No Feature Store vectors"
          description="No persisted observations match this symbol."
        />
      )}
      {result && (
        <>
          <Panel>
            <SectionHeader title="Outcome evidence" />
            <div className="similarity-summary">
              <StatusPill tone={result.evidence_state === 'SUFFICIENT' ? 'success' : 'warning'}>
                {result.evidence_state}
              </StatusPill>
              <span>{result.match_count} matches</span>
              <span>{result.statistics.classified_count} classified outcomes</span>
              <span>Historical win rate: {percent(result.statistics.historical_win_rate)}</span>
            </div>
            {result.evidence_state === 'INSUFFICIENT' && (
              <p role="alert">
                Too few classified persisted outcomes exist for reliable historical statistics. No
                confidence is inferred.
              </p>
            )}
          </Panel>
          {!result.matches.length ? (
            <EmptyState
              title="No comparable history"
              description="No earlier vector met the minimum shared-feature requirement."
            />
          ) : (
            <Panel>
              <SectionHeader
                title="Ranked historical matches"
                description={`Model ${result.model_version}`}
              />
              <div className="similarity-table-wrap">
                <table className="similarity-table">
                  <thead>
                    <tr>
                      <th>Rank</th>
                      <th>Observation</th>
                      <th>Symbol</th>
                      <th>Expiry</th>
                      <th>Similarity</th>
                      <th>Shared</th>
                      <th>Outcome</th>
                      <th>Lineage</th>
                    </tr>
                  </thead>
                  <tbody>
                    {result.matches.map((match) => (
                      <tr key={match.vector_id}>
                        <td>{match.rank}</td>
                        <td>{new Date(match.observed_at).toLocaleString()}</td>
                        <td>{match.underlying_symbol}</td>
                        <td>{match.expiry}</td>
                        <td>{percent(match.similarity_score)}</td>
                        <td>{match.shared_feature_count}</td>
                        <td>
                          {match.outcome?.closing_return == null
                            ? 'Unavailable'
                            : `${Number(match.outcome.closing_return).toFixed(2)}%`}
                        </td>
                        <td>
                          <Link to={`/research/${match.underlying_symbol}?expiry=${match.expiry}`}>
                            Symbol
                          </Link>
                          {' · '}
                          <a href={`/api/v2/features/${match.vector_id}`}>Vector</a>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Panel>
          )}
        </>
      )}
    </div>
  )
}
