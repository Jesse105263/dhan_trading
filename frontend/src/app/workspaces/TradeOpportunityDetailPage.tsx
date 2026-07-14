import { Link, useParams } from 'react-router-dom'
import { tradeOpportunityApi } from '../../api/trade-opportunities'
import { newsEventApi } from '../../api/news-events'
import {
  EmptyState,
  ErrorState,
  PageHeader,
  Panel,
  SectionHeader,
  Skeleton,
  StatusPill,
} from '../../design-system'
import { useReadQuery } from './useReadQuery'
import './trade-opportunities.css'

const show = (value: number | null, suffix = '') =>
  value == null ? 'Unavailable' : `${Number(value).toFixed(2)}${suffix}`

export function TradeOpportunityDetailPage() {
  const { opportunityId = '' } = useParams()
  const query = useReadQuery(
    (signal) => tradeOpportunityApi.detail(opportunityId, signal),
    [opportunityId],
  )
  const eventQuery = useReadQuery(
    (signal) => newsEventApi.opportunity(opportunityId, signal),
    [opportunityId],
  )
  if (query.loading) return <Skeleton label="Loading opportunity evidence" lines={10} />
  if (query.error)
    return (
      <ErrorState
        title="Opportunity unavailable"
        description="The requested persisted opportunity could not be read."
      />
    )
  const item = query.data?.data
  if (!item)
    return <EmptyState title="Opportunity not found" description="No persisted record exists." />
  return (
    <div className="section-stack">
      <PageHeader
        eyebrow="Traceable assessment"
        title={`${item.underlying_symbol} · ${item.expiry}`}
        description="Underlying reference levels derived from classified historical matches; not an execution instruction."
      />
      <Panel>
        <div className="trade-summary">
          <StatusPill tone={item.state === 'ELIGIBLE' ? 'success' : 'warning'}>
            {item.state}
          </StatusPill>
          <span>Score: {show(item.opportunity_score)}</span>
          <span>Evidence quality: {show(item.evidence_quality * 100, '%')}</span>
          <span>Classified: {item.classified_count}</span>
        </div>
      </Panel>
      <Panel>
        <SectionHeader title="Evidence-derived levels" />
        <dl className="trade-levels">
          <div>
            <dt>Entry zone</dt>
            <dd>
              {item.entry_zone_low == null
                ? 'Unavailable'
                : `${show(item.entry_zone_low)}–${show(item.entry_zone_high)}`}
            </dd>
          </div>
          <div>
            <dt>Stop zone</dt>
            <dd>{show(item.stop_zone)}</dd>
          </div>
          <div>
            <dt>Targets</dt>
            <dd>
              {item.target_zones.length
                ? item.target_zones.map((value) => show(value)).join(' / ')
                : 'Unavailable'}
            </dd>
          </div>
          <div>
            <dt>Expected value</dt>
            <dd>{show(item.expected_value, '%')}</dd>
          </div>
          <div>
            <dt>Historical win rate</dt>
            <dd>
              {item.historical_win_rate == null
                ? 'Unavailable'
                : show(item.historical_win_rate * 100, '%')}
            </dd>
          </div>
          <div>
            <dt>Risk/reward</dt>
            <dd>{show(item.risk_reward)}</dd>
          </div>
        </dl>
      </Panel>
      <Panel>
        <SectionHeader title="Reasons for" />
        {item.reasons_for.length ? (
          <ul>
            {item.reasons_for.map((reason) => (
              <li key={reason}>{reason}</li>
            ))}
          </ul>
        ) : (
          <p>No supporting claim is available.</p>
        )}
        <SectionHeader title="Reasons against" />
        <ul>
          {item.reasons_against.map((reason) => (
            <li key={reason}>{reason}</li>
          ))}
        </ul>
      </Panel>
      <Panel>
        <SectionHeader
          title="Upcoming event risk"
          description="Context only; these events do not alter the persisted opportunity calculation."
        />
        {eventQuery.loading ? (
          <Skeleton label="Loading opportunity event context" lines={3} />
        ) : eventQuery.error ? (
          <ErrorState
            title="Event context unavailable"
            description="The opportunity remains unchanged; persisted event context could not be read."
          />
        ) : !eventQuery.data?.data.events.length ? (
          <EmptyState
            title="No linked event context"
            description="No explicitly relevant event was known for the configured context windows."
          />
        ) : (
          <ul>
            {eventQuery.data.data.events.map((context) => (
              <li key={`${context.event_id}-${context.context_type}`}>
                <strong>{context.context_type === 'UPCOMING_RISK' ? 'Upcoming' : 'Recent'}:</strong>{' '}
                {context.event.title} ·{' '}
                {context.event.event_at
                  ? new Date(context.event.event_at).toLocaleString()
                  : 'event time unavailable'}{' '}
                · {context.event.source_reference ?? context.event.source}
              </li>
            ))}
          </ul>
        )}
        <SectionHeader title="Event reasons for" />
        <p>No positive trade reason is inferred from event presence.</p>
        <SectionHeader title="Event reasons against" />
        {eventQuery.data?.data.reasons_against.length ? (
          <ul>
            {eventQuery.data.data.reasons_against.map((reason) => (
              <li key={reason}>{reason}</li>
            ))}
          </ul>
        ) : (
          <p>No scheduled-event risk was linked.</p>
        )}
      </Panel>
      <Panel>
        <SectionHeader title="Exact evidence lineage" />
        {!item.evidence?.length ? (
          <EmptyState
            title="No classified evidence"
            description="Recommendation fields remain unavailable."
          />
        ) : (
          <ol>
            {item.evidence.map((e) => (
              <li key={e.similarity_match_id}>
                {e.underlying_symbol} · {new Date(e.observed_at).toLocaleString()} · similarity{' '}
                {show(e.similarity_score * 100, '%')} ·{' '}
                <a href={`/api/v2/features/${e.matched_vector_id}`}>vector</a> ·{' '}
                <a href={`/api/v2/outcomes/${e.matched_outcome_id}`}>outcome</a>
              </li>
            ))}
          </ol>
        )}
        <p>
          <Link to="/trade-opportunities">Back to opportunities</Link>
        </p>
      </Panel>
    </div>
  )
}
