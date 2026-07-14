import { Link, useSearchParams } from 'react-router-dom'
import { tradeOpportunityApi } from '../../api/trade-opportunities'
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
import './trade-opportunities.css'

const show = (value: number | null, suffix = '') =>
  value == null ? 'Unavailable' : `${Number(value).toFixed(2)}${suffix}`
const tone = (state: string): 'success' | 'warning' | 'neutral' =>
  state === 'ELIGIBLE' ? 'success' : state === 'INSUFFICIENT_EVIDENCE' ? 'warning' : 'neutral'

export function TradeOpportunityPage() {
  const [parameters, setParameters] = useSearchParams({ limit: '50' })
  const key = parameters.toString()
  const query = useReadQuery((signal) => tradeOpportunityApi.list(parameters, signal), [key])
  if (query.loading)
    return <Skeleton label="Loading deterministic trade opportunities" lines={10} />
  if (query.error)
    return (
      <ErrorState
        title="Opportunity evidence unavailable"
        description="Persisted opportunity records could not be read."
      />
    )
  const rows = query.data?.data ?? []
  return (
    <div className="section-stack">
      <PageHeader
        eyebrow="Deterministic evidence"
        title="Trade Opportunities"
        description="Historically supported underlying reference zones. No order is placed and no result is guaranteed."
      />
      <Panel>
        <form
          className="trade-filters"
          onSubmit={(event) => {
            event.preventDefault()
            const form = new FormData(event.currentTarget)
            const next = new URLSearchParams({ limit: '50' })
            const symbolValue = form.get('symbol')
            const stateValue = form.get('state')
            const symbol = typeof symbolValue === 'string' ? symbolValue.trim() : ''
            const state = typeof stateValue === 'string' ? stateValue : ''
            if (symbol) next.set('symbol', symbol.toUpperCase())
            if (state) next.set('state', state)
            setParameters(next)
          }}
        >
          <Input name="symbol" label="Symbol" defaultValue={parameters.get('symbol') ?? ''} />
          <Select name="state" label="Evidence state" defaultValue={parameters.get('state') ?? ''}>
            <option value="">All states</option>
            <option value="ELIGIBLE">Eligible</option>
            <option value="INSUFFICIENT_EVIDENCE">Insufficient evidence</option>
            <option value="NO_OPPORTUNITY">No opportunity</option>
          </Select>
          <button className="ds-button ds-button--primary ds-button--md">Apply filters</button>
        </form>
      </Panel>
      {!rows.length ? (
        <EmptyState
          title="No materialized opportunities"
          description="Run the offline opportunity materializer after auditable similarity runs exist."
        />
      ) : (
        <Panel>
          <div className="trade-table-wrap">
            <table className="trade-table">
              <thead>
                <tr>
                  <th>Rank</th>
                  <th>Symbol</th>
                  <th>State</th>
                  <th>Entry</th>
                  <th>Stop</th>
                  <th>Targets</th>
                  <th>EV</th>
                  <th>Win rate</th>
                  <th>R/R</th>
                  <th>Evidence</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((row) => (
                  <tr key={row.opportunity_id}>
                    <td>{row.rank_position}</td>
                    <td>
                      <Link to={`/trade-opportunities/${row.opportunity_id}`}>
                        {row.underlying_symbol}
                      </Link>
                      <br />
                      <small>{row.expiry}</small>
                    </td>
                    <td>
                      <StatusPill tone={tone(row.state)}>{row.state}</StatusPill>
                    </td>
                    <td>
                      {row.entry_zone_low == null
                        ? 'Unavailable'
                        : `${show(row.entry_zone_low)}–${show(row.entry_zone_high)}`}
                    </td>
                    <td>{show(row.stop_zone)}</td>
                    <td>
                      {row.target_zones.length
                        ? row.target_zones.map((value) => show(value)).join(' / ')
                        : 'Unavailable'}
                    </td>
                    <td>{show(row.expected_value, '%')}</td>
                    <td>
                      {row.historical_win_rate == null
                        ? 'Unavailable'
                        : show(row.historical_win_rate * 100, '%')}
                    </td>
                    <td>{show(row.risk_reward)}</td>
                    <td>
                      {row.classified_count}/{row.match_count}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Panel>
      )}
    </div>
  )
}
