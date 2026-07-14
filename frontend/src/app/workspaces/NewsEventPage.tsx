import { useSearchParams } from 'react-router-dom'
import { newsEventApi } from '../../api/news-events'
import {
  EmptyState,
  ErrorState,
  Input,
  PageHeader,
  Panel,
  Select,
  Skeleton,
  StatusPill,
} from '../../design-system'
import { useReadQuery } from './useReadQuery'
import './news-events.css'

export function NewsEventPage() {
  const [parameters, setParameters] = useSearchParams({ limit: '100' })
  const key = parameters.toString()
  const query = useReadQuery((signal) => newsEventApi.list(parameters, signal), [key])
  if (query.loading) return <Skeleton label="Loading persisted event timeline" lines={10} />
  if (query.error)
    return (
      <ErrorState
        title="Event intelligence unavailable"
        description="Persisted event context could not be read."
      />
    )
  const rows = query.data?.data ?? []
  return (
    <div className="section-stack">
      <PageHeader
        eyebrow="Persisted context"
        title="News & Events"
        description="Explicit source relationships and timestamps only. No sentiment, AI summary, or news-only recommendation."
      />
      <Panel>
        <form
          className="event-filters"
          onSubmit={(event) => {
            event.preventDefault()
            const form = new FormData(event.currentTarget)
            const next = new URLSearchParams({ limit: '100' })
            for (const name of ['symbol', 'sector', 'event_type', 'scheduled']) {
              const value = form.get(name)
              if (typeof value === 'string' && value.trim())
                next.set(name, value.trim().toUpperCase())
            }
            setParameters(next)
          }}
        >
          <Input name="symbol" label="Symbol" defaultValue={parameters.get('symbol') ?? ''} />
          <Input name="sector" label="Sector" defaultValue={parameters.get('sector') ?? ''} />
          <Select
            name="event_type"
            label="Event type"
            defaultValue={parameters.get('event_type') ?? ''}
          >
            <option value="">All types</option>
            <option value="CORPORATE_EARNINGS">Corporate earnings</option>
            <option value="CORPORATE_ACTION">Corporate action</option>
            <option value="EXCHANGE_ANNOUNCEMENT">Exchange announcement</option>
            <option value="MACROECONOMIC">Macroeconomic</option>
            <option value="RBI">RBI</option>
            <option value="SECTOR">Sector</option>
            <option value="MARKET_WIDE">Market-wide</option>
            <option value="COMPANY_NEWS">Company news</option>
          </Select>
          <Select
            name="scheduled"
            label="Schedule"
            defaultValue={parameters.get('scheduled') ?? ''}
          >
            <option value="">All</option>
            <option value="true">Scheduled</option>
            <option value="false">Unscheduled</option>
          </Select>
          <button className="ds-button ds-button--primary ds-button--md">Apply filters</button>
        </form>
      </Panel>
      {!rows.length ? (
        <EmptyState
          title="No persisted event context"
          description="Import an approved local event file or broaden the filters."
        />
      ) : (
        <ol className="event-timeline">
          {rows.map((row) => (
            <li key={row.event_id}>
              <Panel>
                <div className="event-heading">
                  <div>
                    <small>{row.event_type}</small>
                    <h2>{row.title}</h2>
                  </div>
                  <StatusPill tone={row.is_scheduled ? 'info' : 'neutral'}>
                    {row.is_scheduled ? 'SCHEDULED' : 'UNSCHEDULED'}
                  </StatusPill>
                </div>
                <p>{row.summary}</p>
                <dl className="event-meta">
                  <div>
                    <dt>Event time</dt>
                    <dd>
                      {row.event_at ? new Date(row.event_at).toLocaleString() : 'Unavailable'}
                    </dd>
                  </div>
                  <div>
                    <dt>Published</dt>
                    <dd>
                      {row.published_at
                        ? new Date(row.published_at).toLocaleString()
                        : 'Unavailable'}
                    </dd>
                  </div>
                  <div>
                    <dt>Symbols</dt>
                    <dd>
                      {row.market_wide
                        ? 'Market-wide'
                        : row.symbols.join(', ') || 'None explicitly supplied'}
                    </dd>
                  </div>
                  <div>
                    <dt>Source</dt>
                    <dd>{row.source_reference ?? `${row.source}:${row.source_event_id}`}</dd>
                  </div>
                </dl>
              </Panel>
            </li>
          ))}
        </ol>
      )}
    </div>
  )
}
