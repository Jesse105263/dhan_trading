import { Link, useParams } from 'react-router-dom'
import { marketWorkspaceApi } from '../../api/market-workspace'
import {
  EmptyState,
  ErrorState,
  PageHeader,
  Panel,
  Skeleton,
  StatusPill,
} from '../../design-system'
import { useReadQuery } from './useReadQuery'

export function OpportunityDetailPage() {
  const { rankingId = '' } = useParams()
  const query = useReadQuery(
    (signal) => marketWorkspaceApi.opportunity(rankingId, signal),
    [rankingId],
  )
  if (query.loading) return <Skeleton label="Loading opportunity" lines={6} />
  if (query.error || !query.data)
    return (
      <ErrorState
        title="Opportunity not found"
        description="The ranking item does not exist or the read API is unavailable."
        action={<Link to="/scanner">Back to scanner</Link>}
      />
    )
  const item = query.data.data
  return (
    <div className="section-stack">
      <PageHeader
        eyebrow={`Rank ${item.rank_position}`}
        title={`${item.underlying_symbol} · ${item.expiry}`}
        description="Persisted ranking and downstream decision lineage."
        actions={<StatusPill>{item.freshness}</StatusPill>}
      />
      <Panel>
        <dl className="workspace-meta">
          <div>
            <dt>Total score</dt>
            <dd>{Number(item.total_score).toFixed(3)}</dd>
          </div>
          <div>
            <dt>Selection</dt>
            <dd>{item.selection_id ? item.trading_symbol : 'Unavailable'}</dd>
          </div>
          <div>
            <dt>Risk</dt>
            <dd>
              {item.assessment_id
                ? item.approved
                  ? 'Approved'
                  : `Rejected · ${item.rejection_code}`
                : 'Unavailable'}
            </dd>
          </div>
          <div>
            <dt>Signal</dt>
            <dd>{item.signal_id ? 'Generated' : 'Unavailable'}</dd>
          </div>
          <div>
            <dt>Ranking run</dt>
            <dd className="workspace-lineage">{item.ranking_run_id}</dd>
          </div>
          <div>
            <dt>Ranking item</dt>
            <dd className="workspace-lineage">{item.ranking_id}</dd>
          </div>
          <div>
            <dt>Analytics</dt>
            <dd className="workspace-lineage">{item.analytics_id}</dd>
          </div>
          <div>
            <dt>Change lineage</dt>
            <dd className="workspace-lineage">{item.change_id}</dd>
          </div>
        </dl>
        <h2>Ranking explanation</h2>
        {Object.keys(item.explanation).length ? (
          <pre>{JSON.stringify(item.explanation, null, 2)}</pre>
        ) : (
          <EmptyState
            title="No explanation"
            description="This persisted ranking has no explanation fields."
          />
        )}
      </Panel>
    </div>
  )
}
