import type { LucideIcon } from 'lucide-react'

import { Card, PageHeader } from '../../design-system'

export interface PlaceholderPageProps {
  label: string
  description: string
  icon: LucideIcon
}

export function PlaceholderPage({ label, description, icon: Icon }: PlaceholderPageProps) {
  return (
    <div className="shell-page section-stack">
      <PageHeader eyebrow="Version 2 workspace" title={label} description={description} />
      <Card className="shell-placeholder-card">
        <Icon aria-hidden="true" />
        <p>This workspace is intentionally a placeholder.</p>
      </Card>
    </div>
  )
}
