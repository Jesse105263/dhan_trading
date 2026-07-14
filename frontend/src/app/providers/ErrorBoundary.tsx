import { Component, type ErrorInfo, type ReactNode } from 'react'

import { ErrorState } from '../../design-system'

interface ErrorBoundaryState {
  failed: boolean
}

export class ErrorBoundary extends Component<{ children: ReactNode }, ErrorBoundaryState> {
  state: ErrorBoundaryState = { failed: false }

  static getDerivedStateFromError(): ErrorBoundaryState {
    return { failed: true }
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('Application shell render failure.', error, info.componentStack)
  }

  render() {
    if (this.state.failed) {
      return (
        <main id="main-content" className="page-layout container">
          <ErrorState
            title="The application shell could not be displayed"
            description="Reload the page. No trading or data operation was attempted."
          />
        </main>
      )
    }
    return this.props.children
  }
}
