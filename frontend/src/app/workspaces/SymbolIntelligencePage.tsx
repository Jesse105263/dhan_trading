/* eslint-disable @typescript-eslint/no-unused-expressions */
import { useState } from 'react'
import { Link, useParams, useSearchParams } from 'react-router-dom'
import { symbolWorkspaceApi, type SymbolIntelligence } from '../../api/symbol-workspace'
import {
  EmptyState,
  ErrorState,
  Input,
  PageHeader,
  Panel,
  SectionHeader,
  Select,
  Skeleton,
  StatusPill,
} from '../../design-system'
import { useReadQuery } from './useReadQuery'
import './symbol-workspace.css'

const n = (value: string | null | undefined, digits = 2) =>
  value == null ? 'Unavailable' : Number(value).toFixed(digits)
const json = (value: Record<string, unknown>) => JSON.stringify(value, null, 2)

function ScoreBar({ label, value }: { label: string; value: string }) {
  return (
    <div className="score-bar">
      <span>{label}</span>
      <progress max="1" value={Number(value)} aria-label={`${label} ${n(value, 3)}`} />
      <strong>{n(value, 3)}</strong>
    </div>
  )
}
function Summary({ data }: { data: SymbolIntelligence }) {
  const r = data.current_ranking,
    a = data.analytics[0]
  return (
    <>
      <div className="symbol-states">
        <StatusPill>{data.freshness}</StatusPill>
        <StatusPill tone={data.selections.length ? 'success' : 'neutral'}>
          {data.selections.length ? 'Selected' : 'Not selected'}
        </StatusPill>
        <StatusPill tone={data.risk[0]?.approved ? 'success' : 'warning'}>
          {data.risk[0]?.approved ? 'Risk approved' : 'No approval'}
        </StatusPill>
        <StatusPill tone={data.signals.length ? 'info' : 'neutral'}>
          {data.signals.length ? 'Signal present' : 'No signal'}
        </StatusPill>
      </div>
      <div className="symbol-metrics">
        <div>
          <span>Rank</span>
          <strong>{r?.rank_position ?? '—'}</strong>
          <small>
            {data.rank_movement == null
              ? 'No prior rank'
              : `${data.rank_movement > 0 ? '+' : ''}${data.rank_movement} movement`}
          </small>
        </div>
        <div>
          <span>Overall score</span>
          <strong>{r ? n(r.total_score, 3) : '—'}</strong>
        </div>
        <div>
          <span>Spot</span>
          <strong>{a ? n(a.spot_price) : '—'}</strong>
        </div>
        <div>
          <span>Last update</span>
          <strong>{new Date(data.last_update).toLocaleString()}</strong>
        </div>
      </div>
    </>
  )
}

export function SymbolIntelligencePage() {
  const { symbol = '' } = useParams()
  const [params, setParams] = useSearchParams()
  const expiry = params.get('expiry') ?? undefined
  const compare = params.get('compare') ?? ''
  const [compareDraft, setCompareDraft] = useState(compare)
  const [eventType, setEventType] = useState('all')
  const primary = useReadQuery(
    (s) => symbolWorkspaceApi.intelligence(symbol, expiry, s),
    [symbol, expiry],
  )
  const secondary = useReadQuery(
    (s) =>
      compare
        ? symbolWorkspaceApi.intelligence(compare, undefined, s)
        : Promise.resolve(undefined as never),
    [compare],
  )
  if (primary.loading) return <Skeleton label="Loading symbol intelligence" lines={10} />
  if (primary.error || !primary.data)
    return (
      <ErrorState
        title="Symbol intelligence unavailable"
        description="No persisted intelligence exists for this symbol and expiry."
        action={<Link to="/research">Search symbols</Link>}
      />
    )
  const d = primary.data.data,
    r = d.current_ranking,
    a = d.analytics[0]
  const timeline = d.timeline.filter((e) => eventType === 'all' || e.type === eventType)
  return (
    <div className="section-stack">
      <PageHeader
        eyebrow="Symbol intelligence"
        title={`${d.symbol} · ${d.expiry}`}
        description="Persisted evidence only. No recommendation or execution capability."
      />
      <Summary data={d} />
      <Panel>
        <SectionHeader title="Compare symbols" />
        <div className="compare-control">
          <Input
            label="Second symbol"
            value={compareDraft}
            onChange={(e) => setCompareDraft(e.target.value.toUpperCase())}
          />
          <button
            className="ds-button ds-button--secondary ds-button--md"
            onClick={() => {
              const p = new URLSearchParams(params)
              compareDraft ? p.set('compare', compareDraft) : p.delete('compare')
              setParams(p)
            }}
          >
            Compare
          </button>
        </div>
        {compare && secondary.loading ? (
          <Skeleton />
        ) : secondary.data ? (
          <div className="compare-grid">
            <article>
              <h3>{d.symbol}</h3>
              <Summary data={d} />
            </article>
            <article>
              <h3>{secondary.data.data.symbol}</h3>
              <Summary data={secondary.data.data} />
            </article>
          </div>
        ) : compare && secondary.error ? (
          <p>Comparison symbol unavailable.</p>
        ) : null}
      </Panel>
      <div className="symbol-columns">
        <Panel>
          <SectionHeader title="Ranking" />
          {r ? (
            <>
              <ScoreBar label="Overall" value={r.total_score} />
              <ScoreBar label="Liquidity" value={r.liquidity_score} />
              <ScoreBar label="Activity" value={r.activity_score} />
              <ScoreBar label="Volatility" value={r.volatility_score} />
              <ScoreBar label="Directional" value={r.directional_score} />
              <pre>{json(r.explanation)}</pre>
              <h3>Ranking history</h3>
              <ul>
                {d.rankings.map((x) => (
                  <li key={x.ranking_id}>
                    Rank {x.rank_position} · {n(x.total_score, 3)} ·{' '}
                    {new Date(x.source_captured_at).toLocaleString()}
                  </li>
                ))}
              </ul>
            </>
          ) : (
            <EmptyState
              title="Not ranked"
              description="Analytics exist, but no persisted ranking exists for this expiry."
            />
          )}
        </Panel>
        <Panel>
          <SectionHeader title="Option analytics" />
          <dl className="workspace-meta">
            <div>
              <dt>ATM IV</dt>
              <dd>{n(a?.atm_mean_iv)}</dd>
            </div>
            <div>
              <dt>Call / put IV</dt>
              <dd>
                {n(a?.atm_call_iv)} / {n(a?.atm_put_iv)}
              </dd>
            </div>
            <div>
              <dt>Total call / put OI</dt>
              <dd>
                {a?.total_call_oi ?? '—'} / {a?.total_put_oi ?? '—'}
              </dd>
            </div>
            <div>
              <dt>Total PCR</dt>
              <dd>{n(a?.total_pcr)}</dd>
            </div>
            <div>
              <dt>Nearby OI</dt>
              <dd>
                {a?.nearby_call_oi ?? '—'} / {a?.nearby_put_oi ?? '—'}
              </dd>
            </div>
            <div>
              <dt>Liquidity coverage</dt>
              <dd>{n(a?.liquidity_coverage, 3)}</dd>
            </div>
            <div>
              <dt>Price coverage</dt>
              <dd>{n(a?.price_coverage, 3)}</dd>
            </div>
            <div>
              <dt>IV percentile / Greeks</dt>
              <dd>Not persisted</dd>
            </div>
          </dl>
        </Panel>
      </div>
      <div className="symbol-columns">
        <Panel>
          <SectionHeader title="Selection & risk" />
          {d.selections[0] ? (
            <>
              <h3>{d.selections[0].trading_symbol}</h3>
              <p>
                {d.selections[0].option_type} · strike {d.selections[0].strike} · score{' '}
                {n(d.selections[0].contract_score, 3)}
              </p>
              <pre>{json(d.selections[0].explanation)}</pre>
            </>
          ) : (
            <EmptyState title="No selection" description="No persisted selected contract exists." />
          )}
          {d.risk[0] ? (
            <>
              <h3>{d.risk[0].approved ? 'Approved' : 'Rejected'}</h3>
              <p>
                Lots {d.risk[0].approved_lots} · quantity {d.risk[0].approved_quantity} · exposure{' '}
                {d.risk[0].approved_exposure} · maximum loss {d.risk[0].maximum_loss}
              </p>
              <pre>{json(d.risk[0].explanation)}</pre>
            </>
          ) : (
            <EmptyState
              title="No risk decision"
              description="No persisted risk assessment exists."
            />
          )}
        </Panel>
        <Panel>
          <SectionHeader title="Signals" />
          {d.signals.length ? (
            <ul>
              {d.signals.map((s) => (
                <li key={s.signal_id}>
                  <strong>
                    {s.action} · {s.direction}
                  </strong>
                  <p>
                    {new Date(s.calculated_at).toLocaleString()} · confidence{' '}
                    {n(s.confidence_score, 3)}
                  </p>
                  <pre>{json(s.rationale)}</pre>
                </li>
              ))}
            </ul>
          ) : (
            <EmptyState
              title="No signals"
              description="No persisted signal exists for this symbol and expiry."
            />
          )}
        </Panel>
      </div>
      <Panel>
        <SectionHeader
          title="Historical timeline"
          actions={
            <Select
              label="Event type"
              value={eventType}
              onChange={(e) => setEventType(e.target.value)}
            >
              <option value="all">All events</option>
              {['collection', 'analytics', 'ranking', 'selection', 'risk', 'signal'].map((x) => (
                <option key={x}>{x}</option>
              ))}
            </Select>
          }
        />
        {timeline.length ? (
          <ol className="symbol-timeline">
            {timeline.map((e) => (
              <li key={`${e.type}-${e.id}`}>
                <StatusPill>{e.type}</StatusPill>
                <time>{new Date(e.timestamp).toLocaleString()}</time>
                <code>{e.id}</code>
              </li>
            ))}
          </ol>
        ) : (
          <EmptyState title="No timeline events" description="No events match this filter." />
        )}
      </Panel>
      <Panel>
        <SectionHeader title="Lineage" />
        <div className="lineage-flow">
          {[
            ['Ranking', r?.ranking_id],
            ['Selection', d.selections[0]?.selection_id],
            ['Risk', d.risk[0]?.assessment_id],
            ['Signal', d.signals[0]?.signal_id],
          ].map(([label, id]) => (
            <div key={label}>
              <strong>{label}</strong>
              <code>{id ?? 'Unavailable'}</code>
            </div>
          ))}
        </div>
        <SectionHeader title="Related expiries" />
        {d.related.length ? (
          <ul>
            {d.related.map((x) => (
              <li key={x.ranking_id}>
                <Link to={`/research/${d.symbol}?expiry=${x.expiry}`}>
                  {x.expiry} · rank {x.rank_position} · score {n(x.total_score, 3)}
                </Link>
              </li>
            ))}
          </ul>
        ) : (
          <EmptyState
            title="No related opportunities"
            description="No other persisted ranked expiry exists."
          />
        )}
      </Panel>
    </div>
  )
}
