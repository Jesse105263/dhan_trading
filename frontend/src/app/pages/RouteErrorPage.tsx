import { isRouteErrorResponse, useRouteError } from 'react-router-dom'

import { ErrorState } from '../../design-system'

export function RouteErrorPage() {
  const error = useRouteError()
  const description = isRouteErrorResponse(error)
    ? `The route returned ${error.status} ${error.statusText}.`
    : 'The route could not be rendered.'

  return (
    <main id="main-content" className="page-layout container">
      <ErrorState title="Unable to display this page" description={description} />
    </main>
  )
}
