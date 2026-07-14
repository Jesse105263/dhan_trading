import { type FormEvent, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { tradingAnalystApi, type AnalystResponse } from '../../api/trading-analyst'
import {
  Button,
  EmptyState,
  ErrorState,
  Input,
  PageHeader,
  Panel,
  SectionHeader,
  Spinner,
  StatusPill,
} from '../../design-system'
import './trading-analyst.css'

export function TradingAnalystPage() {
  const [parameters] = useSearchParams()
  const [first, setFirst] = useState(parameters.get('opportunity') ?? '')
  const [second, setSecond] = useState('')
  const [question, setQuestion] = useState(
    'Explain this opportunity and its strongest evidence and risks.',
  )
  const [result, setResult] = useState<AnalystResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(false)

  async function submit(event: FormEvent) {
    event.preventDefault()
    setLoading(true)
    setError(false)
    setResult(null)
    try {
      const response = second.trim()
        ? await tradingAnalystApi.compare([first.trim(), second.trim()], question)
        : await tradingAnalystApi.explain(first.trim(), question)
      setResult(response.data)
    } catch {
      setError(true)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="section-stack">
      <PageHeader
        eyebrow="Grounded research"
        title="AI Trading Analyst"
        description="Explains deterministic opportunities using verified application evidence. No execution tools."
      />
      <Panel>
        <form className="analyst-form" onSubmit={(event) => void submit(event)}>
          <Input
            label="Opportunity ID"
            value={first}
            onChange={(event) => setFirst(event.target.value)}
            required
          />
          <Input
            label="Compare opportunity ID (optional)"
            value={second}
            onChange={(event) => setSecond(event.target.value)}
          />
          <label htmlFor="analyst-question">Research question</label>
          <textarea
            id="analyst-question"
            maxLength={2000}
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            required
          />
          <Button type="submit" disabled={loading}>
            {loading ? 'Analyzing…' : second ? 'Compare evidence' : 'Explain opportunity'}
          </Button>
        </form>
      </Panel>
      {loading && <Spinner label="Assembling verified analyst evidence" />}
      {error && (
        <ErrorState
          title="Analyst unavailable"
          description="Verified evidence could not be assembled."
        />
      )}
      {!loading && !error && !result && (
        <EmptyState
          title="Choose a persisted opportunity"
          description="The analyst will not create an opportunity or calculate new trade levels."
        />
      )}
      {result && (
        <Panel>
          <div className="analyst-status">
            <StatusPill tone={result.status === 'REFUSED' ? 'danger' : 'neutral'}>
              {result.status}
            </StatusPill>
            <span>Provider: {result.provider}</span>
          </div>
          <SectionHeader title="Grounded response" />
          <pre className="analyst-answer">{result.answer}</pre>
          <SectionHeader title="Application-attached evidence citations" />
          {result.citations.length ? (
            <ul>
              {result.citations.map((item) => (
                <li key={`${item.type}-${item.id}`}>
                  <a href={citationHref(item.type, item.id)}>{item.citation}</a> · {item.type}
                </li>
              ))}
            </ul>
          ) : (
            <p>No evidence was retrieved.</p>
          )}
          {result.evidence.some((item) => item.evidence_state !== 'ELIGIBLE') && (
            <p className="analyst-warning">
              <strong>INSUFFICIENT_EVIDENCE</strong> — trade levels and statistics are unavailable.
            </p>
          )}
        </Panel>
      )}
    </div>
  )
}

function citationHref(type: string, id: string) {
  if (type === 'feature_vector') return `/api/v2/features/${id}`
  if (type === 'historical_outcome') return `/api/v2/outcomes/${id}`
  if (type === 'market_event') return `/api/v2/events/${id}`
  if (type === 'market_memory') return `/api/v2/memory/snapshots/${id}`
  if (type === 'similarity_run') return `/api/v2/similarity/runs/${id}`
  return `/api/v2/trade-opportunities/${id}`
}
