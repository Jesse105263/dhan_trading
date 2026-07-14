import { FormEvent, useState } from 'react'
import { Link } from 'react-router-dom'
import { symbolWorkspaceApi } from '../../api/symbol-workspace'
import { Button, EmptyState, ErrorState, Input, PageHeader, Skeleton } from '../../design-system'
import { useReadQuery } from './useReadQuery'

export function SymbolSearchPage() {
  const [draft, setDraft] = useState('')
  const [query, setQuery] = useState('')
  const result = useReadQuery((signal) => symbolWorkspaceApi.search(query, signal), [query])
  const submit = (e: FormEvent) => {
    e.preventDefault()
    setQuery(draft.trim().toUpperCase())
  }
  return (
    <div className="section-stack">
      <PageHeader
        eyebrow="Persisted research"
        title="Symbol Intelligence"
        description="Search persisted symbols before assessing whether an opportunity deserves attention."
      />
      <form onSubmit={submit} className="symbol-search">
        <Input
          label="Search symbol"
          value={draft}
          onChange={(e) => setDraft(e.target.value.toUpperCase())}
          autoFocus
        />
        <Button>Search</Button>
      </form>
      {result.loading ? (
        <Skeleton />
      ) : result.error ? (
        <ErrorState
          title="Search unavailable"
          description="Persisted symbol search could not be loaded."
        />
      ) : !result.data?.data.length ? (
        <EmptyState
          title="No symbols found"
          description="No persisted analytics match this symbol search."
        />
      ) : (
        <ul className="symbol-results">
          {result.data.data.map((item) => (
            <li key={item.underlying_symbol}>
              <Link to={`/research/${item.underlying_symbol}`}>{item.underlying_symbol}</Link>
              <span>{item.expiries.join(', ')}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
