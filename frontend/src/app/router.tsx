import { createBrowserRouter } from 'react-router-dom'

import { navigationItems } from './navigation'
import { NotFoundPage } from './pages/NotFoundPage'
import { PlaceholderPage } from './pages/PlaceholderPage'
import { RouteErrorPage } from './pages/RouteErrorPage'
import { AppShell } from './shell/AppShell'
import { MarketOverviewPage } from './workspaces/MarketOverviewPage'
import { OpportunityDetailPage } from './workspaces/OpportunityDetailPage'
import { OpportunityScannerPage } from './workspaces/OpportunityScannerPage'

const [home, ...workspaces] = navigationItems

if (!home) throw new Error('A home route is required.')

export const router = createBrowserRouter([
  {
    path: '/',
    element: <AppShell />,
    errorElement: <RouteErrorPage />,
    children: [
      {
        index: true,
        element: (
          <PlaceholderPage label={home.label} description={home.description} icon={home.icon} />
        ),
      },
      { path: 'market', element: <MarketOverviewPage /> },
      { path: 'scanner', element: <OpportunityScannerPage /> },
      { path: 'opportunities/:rankingId', element: <OpportunityDetailPage /> },
      ...workspaces
        .filter((route) => !['/market', '/scanner'].includes(route.path))
        .map((route) => ({
          path: route.path.slice(1),
          element: (
            <PlaceholderPage
              label={route.label}
              description={route.description}
              icon={route.icon}
            />
          ),
        })),
      { path: '*', element: <NotFoundPage /> },
    ],
  },
])
