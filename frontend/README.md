# Dhan Trading Platform Frontend

## Purpose

This directory contains the isolated Version 2 browser application. Keeping the
Node project under `frontend/` prevents its package management, build output and
tooling from changing the stable Python application layout.

V2.0.2 provides foundation only: one placeholder route, a typed API-client pattern,
environment handling and build/test/lint/format tooling. It contains no product
workspace, authentication, chart, market-data request or business behavior.

V2.0.3 adds reusable design-system tokens and components under
`src/design-system/`. See `docs/DESIGN_SYSTEM.md`.

V2.0.4 adds the responsive application shell, nested placeholder routes and
shell-only providers. It makes no API request and implements no named workspace.
See `docs/APPLICATION_SHELL.md`.

## Requirements

- Node.js 26
- npm 11

Use the committed `package-lock.json` and install with:

```bash
cd frontend
npm ci
```

## Commands

```bash
npm run dev
npm run build
npm test
npm run lint
npm run format:check
```

The development server binds to `127.0.0.1`. Copy `.env.example` to `.env.local`
only when local overrides are needed. Vite exposes `VITE_` variables to browser
code, so they must never contain Dhan, database, webhook or model-provider secrets.

## Layout

```text
frontend/
├── public/                 Static public assets when needed
├── src/
│   ├── api/                HTTP transport abstractions
│   ├── app/                Shell, providers, routes and placeholder pages
│   ├── config/             Validated browser environment
│   ├── design-system/      Reusable tokens, styles and components
│   └── test/               Shared test setup
├── package.json            npm scripts and dependency declarations
├── tsconfig*.json          Browser and tooling TypeScript projects
└── vite.config.ts          Build, test and loopback development configuration
```

## Dependency Policy

- Runtime packages must provide product capabilities that the browser platform
  cannot supply clearly and maintainably.
- Native `fetch` is the API transport; no HTTP-client package is needed.
- React Router establishes route composition for later workspaces without coupling
  routes to the backend.
- Vitest shares Vite's TypeScript transformation, and Testing Library verifies
  accessible behavior rather than component implementation details.
- ESLint owns correctness rules; Prettier owns formatting. Their configurations do
  not compete.
- Dependencies are added only in the milestone that needs them and must be pinned
  through `package-lock.json`.
- Lucide is the single icon system; decorative icons are hidden from assistive
  technology and icon-only controls require accessible labels.

## API Boundary

The frontend will communicate only through versioned HTTP application APIs. The
client abstraction accepts relative paths and defaults to same-origin credentials.
It does not currently call an endpoint.

`/api/v1` remains unchanged and continues serving existing Version 1 consumers.
No `/api/v2` endpoint is introduced by this milestone. Future product milestones
will add only the read projections they require.

## Conventions

- TypeScript strict mode is required.
- Components use semantic HTML and are tested by accessible role or visible text.
- Business calculations and database access never belong in the frontend.
- Environment access is centralized under `src/config`.
- API transport is centralized under `src/api` and remains separate from route UI.
- Formatting must pass before review; generated `dist/`, coverage and dependency
  directories are not committed.
