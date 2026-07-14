import { Menu, ShieldCheck, X } from 'lucide-react'
import { useEffect } from 'react'
import { NavLink, Outlet, useLocation } from 'react-router-dom'

import { Button, StatusPill } from '../../design-system'
import { navigationItems } from '../navigation'
import { statusMetadata, useApplication } from '../providers'

export function AppShell() {
  const { status, navigationOpen, setNavigationOpen } = useApplication()
  const location = useLocation()
  const currentStatus = statusMetadata[status]

  useEffect(() => setNavigationOpen(false), [location.pathname, setNavigationOpen])

  return (
    <div className="shell">
      <a className="shell-skip-link" href="#main-content">
        Skip to main content
      </a>
      <header className="shell-header">
        <Button
          variant="quiet"
          size="sm"
          className="shell-menu-button"
          aria-label={navigationOpen ? 'Close navigation' : 'Open navigation'}
          aria-expanded={navigationOpen}
          aria-controls="primary-navigation"
          onClick={() => setNavigationOpen(!navigationOpen)}
        >
          {navigationOpen ? <X aria-hidden="true" /> : <Menu aria-hidden="true" />}
        </Button>
        <NavLink to="/" className="shell-brand" aria-label="Dhan Trading Platform home">
          <span className="shell-brand__mark" aria-hidden="true">
            D
          </span>
          <span>
            <strong>Dhan Trading Platform</strong>
            <small>Private workspace · Version 2</small>
          </span>
        </NavLink>
        <span className="shell-header__safety">
          <ShieldCheck aria-hidden="true" /> No live execution
        </span>
      </header>

      {navigationOpen && (
        <button
          className="shell-nav-scrim"
          aria-label="Close navigation"
          onClick={() => setNavigationOpen(false)}
        />
      )}
      <aside className={`shell-sidebar${navigationOpen ? ' shell-sidebar--open' : ''}`}>
        <nav id="primary-navigation" className="shell-navigation" aria-label="Primary navigation">
          {navigationItems.map(({ path, label, icon: Icon, end }) => (
            <NavLink
              key={path}
              to={path}
              end={end}
              className={({ isActive }) =>
                `shell-nav-link${isActive ? ' shell-nav-link--active' : ''}`
              }
            >
              <Icon aria-hidden="true" />
              <span>{label}</span>
            </NavLink>
          ))}
        </nav>
      </aside>

      <main id="main-content" className="shell-main" tabIndex={-1}>
        <Outlet />
      </main>

      <footer className="shell-status-bar" aria-label="Application status">
        <StatusPill tone={currentStatus.tone}>{currentStatus.label}</StatusPill>
        <span>Shell status is a placeholder and is not connected to the backend.</span>
      </footer>
    </div>
  )
}
