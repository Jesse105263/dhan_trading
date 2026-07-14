import { FormEvent, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { marketWorkspaceApi, type Opportunity } from '../../api/market-workspace'
import {
  Button,
  EmptyState,
  ErrorState,
  Input,
  PageHeader,
  Select,
  Skeleton,
  StatusPill,
  TableShell,
  Toolbar,
} from '../../design-system'
import { useReadQuery } from './useReadQuery'
import './workspace.css'

const score = (value: string) => Number(value).toFixed(3)
const time = (value: string) => new Date(value).toLocaleString()
const availabilityFilters = [
  ['selection', 'Selection'],
  ['risk_approved', 'Risk approved'],
  ['signal', 'Signal'],
] as const

export function OpportunityScannerPage() {
  const [draft, setDraft] = useState({
    symbol: '',
    expiry: '',
    minimum_score: '',
    freshness: '',
    selection: '',
    risk_approved: '',
    signal: '',
  })
  const [filters, setFilters] = useState(draft)
  const [sort, setSort] = useState('rank')
  const [direction, setDirection] = useState('asc')
  const parameters = useMemo(() => {
    const p = new URLSearchParams({ limit: '50', sort, direction })
    Object.entries(filters).forEach(([k, v]) => {
      if (v) p.set(k, v)
    })
    return p
  }, [filters, sort, direction])
  const query = useReadQuery(
    (signal) => marketWorkspaceApi.opportunities(parameters, signal),
    [parameters.toString()],
  )
  const submit = (event: FormEvent) => {
    event.preventDefault()
    setFilters({ ...draft })
  }
  const changeSort = (field: string) => {
    if (sort === field) setDirection(direction === 'asc' ? 'desc' : 'asc')
    else {
      setSort(field)
      setDirection(field === 'score' || field === 'captured_at' ? 'desc' : 'asc')
    }
  }
  const columns = useMemo(
    () => [
      {
        key: 'rank',
        header: 'Rank',
        sortable: true,
        render: (item: Opportunity) => item.rank_position,
      },
      {
        key: 'symbol',
        header: 'Symbol',
        sortable: true,
        render: (item: Opportunity) => <strong>{item.underlying_symbol}</strong>,
      },
      { key: 'expiry', header: 'Expiry', render: (item: Opportunity) => item.expiry },
      {
        key: 'score',
        header: 'Score',
        sortable: true,
        render: (item: Opportunity) => (
          <span className="workspace-score">{score(item.total_score)}</span>
        ),
      },
      {
        key: 'liquidity',
        header: 'Liquidity',
        render: (item: Opportunity) => score(item.liquidity_score),
      },
      {
        key: 'activity',
        header: 'Activity',
        render: (item: Opportunity) => score(item.activity_score),
      },
      {
        key: 'volatility',
        header: 'Volatility',
        render: (item: Opportunity) => score(item.volatility_score),
      },
      {
        key: 'directional',
        header: 'Directional',
        render: (item: Opportunity) => score(item.directional_score),
      },
      {
        key: 'captured_at',
        header: 'Captured',
        sortable: true,
        render: (item: Opportunity) => time(item.source_captured_at),
      },
      {
        key: 'freshness',
        header: 'Freshness',
        render: (item: Opportunity) => (
          <StatusPill
            tone={
              item.freshness === 'current'
                ? 'success'
                : item.freshness === 'aging'
                  ? 'warning'
                  : 'danger'
            }
          >
            {item.freshness}
          </StatusPill>
        ),
      },
      {
        key: 'selection',
        header: 'Selected',
        render: (item: Opportunity) => (item.selection_available ? 'Yes' : '—'),
      },
      {
        key: 'risk',
        header: 'Risk',
        render: (item: Opportunity) => (item.risk_approved ? 'Approved' : '—'),
      },
      {
        key: 'signal',
        header: 'Signal',
        render: (item: Opportunity) => (item.signal_available ? 'Yes' : '—'),
      },
      {
        key: 'detail',
        header: 'Detail',
        render: (item: Opportunity) => (
          <Link className="workspace-link" to={`/opportunities/${item.ranking_id}`}>
            Inspect
          </Link>
        ),
      },
    ],
    [],
  )
  return (
    <div className="section-stack">
      <PageHeader
        eyebrow="Persisted rankings"
        title="Opportunity Scanner"
        description="Latest ranked opportunities with downstream decision availability. Rankings are evidence, not profit guarantees."
      />
      <form onSubmit={submit}>
        <Toolbar label="Opportunity filters" className="workspace-filters">
          <Input
            label="Symbol"
            value={draft.symbol}
            onChange={(e) => setDraft({ ...draft, symbol: e.target.value.toUpperCase() })}
          />
          <Input
            label="Expiry"
            type="date"
            value={draft.expiry}
            onChange={(e) => setDraft({ ...draft, expiry: e.target.value })}
          />
          <Input
            label="Minimum score"
            type="number"
            min="0"
            max="1"
            step="0.01"
            value={draft.minimum_score}
            onChange={(e) => setDraft({ ...draft, minimum_score: e.target.value })}
          />
          <Select
            label="Freshness"
            value={draft.freshness}
            onChange={(e) => setDraft({ ...draft, freshness: e.target.value })}
          >
            <option value="">Any</option>
            <option value="current">Current</option>
            <option value="aging">Aging</option>
            <option value="stale">Stale</option>
          </Select>
          {availabilityFilters.map(([key, label]) => (
            <Select
              key={key}
              label={label}
              value={draft[key as keyof typeof draft]}
              onChange={(e) => setDraft({ ...draft, [key]: e.target.value })}
            >
              <option value="">Any</option>
              <option value="true">Yes</option>
              <option value="false">No</option>
            </Select>
          ))}
          <Button type="submit">Apply</Button>
        </Toolbar>
      </form>
      {query.loading ? (
        <Skeleton label="Loading opportunities" lines={8} />
      ) : query.error || !query.data ? (
        <ErrorState
          title="Scanner unavailable"
          description="The API rejected the filters or could not read persisted rankings."
          action={<Button onClick={query.retry}>Retry</Button>}
        />
      ) : query.data.data.length === 0 ? (
        <EmptyState
          title="No ranked opportunities"
          description="The latest ranking run is empty or no opportunities match these filters."
        />
      ) : (
        <TableShell
          className="workspace-table"
          caption={`${query.data.page.count} of ${query.data.page.total} opportunities`}
          columns={columns}
          rows={query.data.data}
          rowKey={(item) => item.ranking_id}
          onSortRequest={changeSort}
        />
      )}
    </div>
  )
}
