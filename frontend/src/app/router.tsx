import { createBrowserRouter } from 'react-router-dom'

import { navigationItems } from './navigation'
import { NotFoundPage } from './pages/NotFoundPage'
import { PlaceholderPage } from './pages/PlaceholderPage'
import { RouteErrorPage } from './pages/RouteErrorPage'
import { AppShell } from './shell/AppShell'

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
      ...workspaces.map((route) => ({
        path: route.path.slice(1),
        element: (
          <PlaceholderPage label={route.label} description={route.description} icon={route.icon} />
        ),
      })),
      { path: '*', element: <NotFoundPage /> },
    ],
  },
])
