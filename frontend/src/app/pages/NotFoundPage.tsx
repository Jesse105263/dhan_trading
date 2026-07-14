import { Link } from 'react-router-dom'

import { ErrorState } from '../../design-system'

export function NotFoundPage() {
  return (
    <div className="shell-page">
      <ErrorState
        title="Page not found"
        description="The requested workspace route does not exist."
        action={
          <Link className="ds-button ds-button--secondary ds-button--md" to="/">
            Return home
          </Link>
        }
      />
    </div>
  )
}
