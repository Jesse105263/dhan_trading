# Version 2 Application Shell

## Purpose

V2.0.4 provides the reusable browser frame for future workspaces. It contains no
market data, API request, authentication, chart, command or business policy. Every
named workspace route renders only a title and short placeholder description.

## Layout

The `AppShell` is a nested React Router layout with four persistent regions:

1. an application header with product identity and the no-live-execution boundary;
2. a primary navigation rail;
3. a main outlet for child routes; and
4. a status footer that explicitly reports its disconnected placeholder state.

Desktop uses the full navigation rail. Tablet uses a compact icon rail with labels
available as accessible names and tooltips. Mobile hides the rail until the labelled
menu control opens it over a dismissible scrim. Motion is limited and respects the
design system's reduced-motion rule.

## Routes

| Path | Placeholder title |
| --- | --- |
| `/` | Home |
| `/market` | Market Overview |
| `/scanner` | Scanner |
| `/research` | Symbol Research |
| `/signals` | Signals |
| `/evaluation` | Replay & Backtesting |
| `/paper` | Paper Portfolio |
| `/operations` | Operations |
| `/copilot` | Copilot |
| `/settings` | Settings |
| any unmatched path | Page not found |

The root layout route owns the shell, the index route owns Home, and the wildcard
route keeps the not-found state inside the shell. Route definitions and navigation
metadata remain centralized under `frontend/src/app`.

## Provider Hierarchy

The entry point composes providers in this order:

```text
ErrorBoundary
└── ThemeProvider
    └── ApplicationProvider
        └── LoadingBoundary
            └── RouterProvider
```

`ThemeProvider` fixes the approved light theme while retaining semantic tokens for
future dark mode. `ApplicationProvider` contains shell state only: mobile-navigation
visibility, placeholder platform status, modal and drawer requests, and transient
toasts. `LoadingBoundary` supplies a reusable shell fallback; routes are not yet
lazy-loaded. The application-level error boundary prevents a render failure from
leaving a blank page.

The modal host, drawer host and polite toast region reuse design-system primitives.
They have no business consumers in this milestone.

## Placeholder Statuses

The shell defines presentation metadata for backend unavailable, loading, offline
and maintenance. The initial footer shows backend unavailable and states that the
frontend is not connected to the backend. No connectivity probe or API client call
changes these values.

## Accessibility Contract

- Header, navigation, main and status-footer landmarks remain explicit.
- A keyboard-visible skip link targets the main outlet.
- Active navigation uses `aria-current="page"`.
- Mobile navigation exposes its controlled region and expanded state.
- Icon-only controls have accessible names; decorative icons are hidden.
- Focus, contrast, target sizing and reduced motion inherit the design system.
- Route and provider tests query the rendered interface by accessible role or text.

## Boundaries

The shell imports no API client and performs no request. `/api/v1` remains unchanged;
no `/api/v2` exists. Python code, repositories, services, migrations and the database
schema remain untouched. Paper trading and Copilot retain every Version 1 safety
boundary, and placeholder routes confer no execution capability.
