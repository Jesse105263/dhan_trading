import { Link } from 'react-router-dom'
import { marketWorkspaceApi } from '../../api/market-workspace'
import {
  Button,
  Card,
  EmptyState,
  ErrorState,
  PageHeader,
  Panel,
  SectionHeader,
  Skeleton,
  StatusPill,
} from '../../design-system'
import { useReadQuery } from './useReadQuery'
import './workspace.css'

const tone = (state: string) =>
  state === 'current' ? 'success' : state === 'aging' ? 'warning' : 'danger'
const time = (value?: string | null) => (value ? new Date(value).toLocaleString() : 'Unavailable')

export function MarketOverviewPage() {
  const query = useReadQuery((signal) => marketWorkspaceApi.overview(signal), [])
  if (query.loading)
    return (
      <>
        <PageHeader
          eyebrow="Market intelligence"
          title="Market Overview"
          description="Loading persisted platform state."
        />
        <Skeleton lines={6} />
      </>
    )
  if (query.error || !query.data)
    return (
      <ErrorState
        title="Market overview unavailable"
        description="The read API or database could not provide the persisted overview."
        action={<Button onClick={query.retry}>Retry</Button>}
      />
    )
  const data = query.data
  return (
    <div className="section-stack">
      <PageHeader
        eyebrow="Market intelligence"
        title="Market Overview"
        description="Persisted health, freshness and decision-pipeline coverage—never live market data."
        actions={<StatusPill tone={tone(data.freshness.state)}>{data.freshness.state}</StatusPill>}
      />
      <div className="workspace-grid">
        {Object.entries({
          Ranked: data.counts.ranked,
          Selected: data.counts.selections,
          Approved: data.counts.risk_approved,
          Rejected: data.counts.risk_rejected,
          Signals: data.counts.signals,
        }).map(([label, value]) => (
          <Card className="workspace-metric" key={label}>
            <strong>{value}</strong>
            <span>{label}</span>
          </Card>
        ))}
      </div>
      <div className="workspace-summary">
        <Panel>
          <SectionHeader title="Freshness and lineage" />
          <dl className="workspace-meta">
            <div>
              <dt>Database</dt>
              <dd>{data.platform.database_ready ? 'Ready' : 'Unavailable'}</dd>
            </div>
            <div>
              <dt>Source timestamp</dt>
              <dd>{time(data.freshness.source_timestamp)}</dd>
            </div>
            <div>
              <dt>Latest option run</dt>
              <dd className="workspace-lineage">
                {data.latest_option_run?.run_id ?? 'Unavailable'}
              </dd>
            </div>
            <div>
              <dt>Latest ranking run</dt>
              <dd className="workspace-lineage">
                {data.latest_ranking_run?.ranking_run_id ?? 'Unavailable'}
              </dd>
            </div>
            <div>
              <dt>Pipeline completion</dt>
              <dd>{time(data.latest_option_run?.completed_at)}</dd>
            </div>
            <div>
              <dt>Ranking calculated</dt>
              <dd>{time(data.latest_ranking_run?.calculated_at)}</dd>
            </div>
          </dl>
          <p>
            <Link className="workspace-link" to="/scanner">
              Open Opportunity Scanner →
            </Link>
          </p>
        </Panel>
        <Panel>
          <SectionHeader title="Recent failures" description="Sanitized persisted records" />
          {data.recent_failures.length === 0 ? (
            <EmptyState
              title="No recent failures"
              description="No persisted pipeline failures are available."
            />
          ) : (
            <ul className="workspace-failures">
              {data.recent_failures.map((failure) => (
                <li key={failure.id}>
                  <strong>
                    {failure.stage_name}
                    {failure.symbol ? ` · ${failure.symbol}` : ''}
                  </strong>
                  <div>
                    {failure.error_type}: {failure.error_message}
                  </div>
                  <small>{time(failure.occurred_at)}</small>
                </li>
              ))}
            </ul>
          )}
        </Panel>
      </div>
    </div>
  )
}
