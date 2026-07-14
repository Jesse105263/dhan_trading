import type { ReactNode } from 'react'

import { Panel, Spinner } from '../../design-system'

export function LoadingBoundary({
  loading,
  label = 'Loading page',
  children,
}: {
  loading: boolean
  label?: string
  children: ReactNode
}) {
  if (!loading) return children
  return (
    <Panel className="shell-loading-boundary">
      <Spinner label={label} />
      <span>{label}</span>
    </Panel>
  )
}
