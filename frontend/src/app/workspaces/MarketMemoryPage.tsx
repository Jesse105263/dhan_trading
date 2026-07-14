import { useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { marketMemoryApi, type MemorySnapshot } from '../../api/market-memory'
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
import './market-memory.css'

const display = (value: string | number | null | undefined) =>
  value == null ? 'Unavailable' : String(value)

function Evolution({ rows, feature }: { rows: MemorySnapshot[]; feature: string }) {
  const points = rows
    .slice()
    .reverse()
    .map((row) => Number(row.features[feature]))
    .filter(Number.isFinite)
  if (points.length < 2) return <p>At least two numeric observations are needed.</p>
  const minimum = Math.min(...points),
    maximum = Math.max(...points),
    span = maximum - minimum || 1
  const path = points
    .map((value, index) => {
      const x = (index / (points.length - 1)) * 100
      const y = 36 - ((value - minimum) / span) * 32
      return `${x},${y}`
    })
    .join(' ')
  return (
    <svg
      className="memory-evolution"
      viewBox="0 0 100 40"
      role="img"
      aria-label={`${feature} evolution`}
    >
      <polyline points={path} />
    </svg>
  )
}

export function MarketMemoryPage() {
  const [parameters, setParameters] = useSearchParams({ symbol: '', limit: '50' })
  const [symbol, setSymbol] = useState(parameters.get('symbol') ?? '')
  const [expiry, setExpiry] = useState(parameters.get('expiry') ?? '')
  const [feature, setFeature] = useState('atm_mean_iv')
  const [selected, setSelected] = useState<string[]>([])
  const queryKey = parameters.toString()
  const query = useReadQuery((signal) => marketMemoryApi.list(parameters, signal), [queryKey])
  const comparison = useReadQuery(
    (signal) =>
      selected.length === 2
        ? marketMemoryApi.compare(selected[0]!, selected[1]!, signal)
        : Promise.resolve(undefined as never),
    [selected.join(',')],
  )
  const rows = query.data?.data ?? []
  const features = query.data?.features ?? []
  const compareData = selected.length === 2 ? comparison.data?.data : undefined
  const filteredChanges = useMemo(() => compareData?.changes ?? [], [compareData])

  if (!parameters.get('symbol'))
    return (
      <div className="section-stack">
        <PageHeader
          eyebrow="Historical evidence"
          title="Market Memory"
          description="Query immutable persisted observations before relying on market behavior."
        />
        <Panel>
          <form
            className="memory-filters"
            onSubmit={(event) => {
              event.preventDefault()
              setParameters({
                symbol: symbol.trim().toUpperCase(),
                ...(expiry && { expiry }),
                limit: '50',
              })
            }}
          >
            <Input
              label="Symbol"
              value={symbol}
              onChange={(event) => setSymbol(event.target.value.toUpperCase())}
              required
            />
            <Input
              label="Expiry"
              type="date"
              value={expiry}
              onChange={(event) => setExpiry(event.target.value)}
            />
            <button className="ds-button ds-button--primary ds-button--md">Load history</button>
          </form>
        </Panel>
        <EmptyState
          title="Choose a symbol"
          description="Market Memory reads only snapshots already persisted by Version 1 pipelines."
        />
      </div>
    )
  if (query.loading) return <Skeleton label="Loading market memory" lines={10} />
  if (query.error)
    return (
      <ErrorState
        title="Market Memory unavailable"
        description="The persisted snapshot history could not be read."
      />
    )
  return (
    <div className="section-stack">
      <PageHeader
        eyebrow="Historical evidence"
        title={`Market Memory · ${parameters.get('symbol')}`}
        description="Immutable observations and deterministic comparisons. No recommendation is generated."
      />
      <Panel>
        <form
          className="memory-filters"
          onSubmit={(event) => {
            event.preventDefault()
            setSelected([])
            setParameters({
              symbol: symbol.trim().toUpperCase(),
              ...(expiry && { expiry }),
              limit: '50',
            })
          }}
        >
          <Input
            label="Symbol"
            value={symbol}
            onChange={(event) => setSymbol(event.target.value.toUpperCase())}
            required
          />
          <Input
            label="Expiry"
            type="date"
            value={expiry}
            onChange={(event) => setExpiry(event.target.value)}
          />
          <Select
            label="Feature evolution"
            value={feature}
            onChange={(event) => setFeature(event.target.value)}
          >
            {features.map((name) => (
              <option key={name}>{name}</option>
            ))}
          </Select>
          <button className="ds-button ds-button--primary ds-button--md">Apply</button>
        </form>
      </Panel>
      {!rows.length ? (
        <EmptyState
          title="No snapshots"
          description="No persisted option-analytics observations match these filters."
        />
      ) : (
        <>
          <Panel>
            <SectionHeader title="Feature evolution" />
            <Evolution rows={rows} feature={feature} />
            <p>
              {feature}: {rows.map((row) => display(row.features[feature])).join(' → ')}
            </p>
          </Panel>
          <Panel>
            <SectionHeader
              title="Historical snapshots"
              description="Select exactly two observations to compare."
            />
            <div className="memory-table-wrap">
              <table className="memory-table">
                <thead>
                  <tr>
                    <th scope="col">Compare</th>
                    <th scope="col">Captured</th>
                    <th scope="col">Expiry</th>
                    <th scope="col">Freshness</th>
                    <th scope="col">Rank</th>
                    <th scope="col">Score</th>
                    <th scope="col">ATM IV</th>
                    <th scope="col">Spot</th>
                    <th scope="col">Lineage</th>
                  </tr>
                </thead>
                <tbody>
                  {rows.map((row) => (
                    <tr key={row.snapshot_id}>
                      <td>
                        <input
                          type="checkbox"
                          aria-label={`Compare snapshot ${row.snapshot_id}`}
                          checked={selected.includes(row.snapshot_id)}
                          onChange={() =>
                            setSelected((current) =>
                              current.includes(row.snapshot_id)
                                ? current.filter((id) => id !== row.snapshot_id)
                                : current.length < 2
                                  ? [...current, row.snapshot_id]
                                  : [current[1]!, row.snapshot_id],
                            )
                          }
                        />
                      </td>
                      <td>
                        <time>{new Date(row.captured_at).toLocaleString()}</time>
                      </td>
                      <td>{row.expiry}</td>
                      <td>
                        <StatusPill tone={row.freshness === 'stale' ? 'warning' : 'neutral'}>
                          {row.freshness}
                        </StatusPill>
                      </td>
                      <td>{display(row.features.rank_position)}</td>
                      <td>{display(row.features.total_score)}</td>
                      <td>{display(row.features.atm_mean_iv)}</td>
                      <td>{display(row.features.spot_price)}</td>
                      <td>
                        <a href={`/api/v2/memory/snapshots/${row.snapshot_id}`}>Snapshot detail</a>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Panel>
          <Panel>
            <SectionHeader title="Snapshot comparison" />
            {selected.length !== 2 ? (
              <EmptyState
                title="Select two snapshots"
                description="The comparison reports only persisted fields whose values changed."
              />
            ) : comparison.loading ? (
              <Skeleton />
            ) : comparison.error ? (
              <ErrorState
                title="Comparison unavailable"
                description="The two observations could not be compared."
              />
            ) : filteredChanges.length ? (
              <dl className="memory-changes">
                {filteredChanges.map((change) => (
                  <div key={change.feature}>
                    <dt>{change.feature}</dt>
                    <dd>
                      {display(change.previous)} <span aria-hidden="true">→</span>{' '}
                      {display(change.current)}
                    </dd>
                  </div>
                ))}
              </dl>
            ) : (
              <EmptyState
                title="No changed fields"
                description="All supported persisted features are equal."
              />
            )}
          </Panel>
        </>
      )}
    </div>
  )
}
