# Version 2 Frontend Foundation

## Repository Layout

The frontend is a self-contained npm project under `frontend/` rather than a set
of Node files at the Python repository root. This keeps package management, build
artifacts and editor/tool configuration from changing the stable Python project.

```text
frontend/
├── public/                 Static public assets
├── src/
│   ├── api/                HTTP transport and tests
│   ├── app/                Shell, providers, routes and placeholder pages
│   ├── config/             Browser-environment validation
│   ├── design-system/      Tokens, global styles and reusable UI primitives
│   └── test/               Shared test setup
├── .env.example
├── package.json
├── package-lock.json
├── tsconfig*.json
└── vite.config.ts
```

See `frontend/README.md` for file-level conventions.

## Dependencies

Runtime:

- React and React DOM: browser rendering and component composition.
- React Router: explicit route composition for future workspaces.

Development:

- TypeScript: strict static checking.
- Vite and its React plugin: development and production builds.
- Vitest: tests using the same TypeScript transformation as the build.
- jsdom and Testing Library: accessible component behavior in a browser-like test
  environment.
- ESLint, TypeScript ESLint and React lint plugins: correctness and framework rules.
- Prettier and its ESLint compatibility configuration: deterministic formatting
  without conflicting lint rules.
- React and Node type packages: compile-time definitions only.

`lucide-react` is the single icon dependency introduced by V2.0.3. Its SVG React
components are tree-shakeable and avoid icon-font assets. No Axios/fetch wrapper,
global state manager, UI kit, CSS framework, chart package, authentication library
or API-schema generator is included. Native `fetch` remains sufficient for the
transport foundation.

## Local Development

Node and npm are managed outside the repository. From the repository root:

```bash
cd frontend
npm ci
npm run dev
```

The development server binds to `127.0.0.1`. It performs no API request. If a later
milestone needs a development proxy, copy `.env.example` to `.env.local` and set
`VITE_API_PROXY_TARGET` to an explicitly approved local API origin.

Never place PostgreSQL, Redis, Dhan, webhook or model-provider credentials in a
`VITE_` variable because Vite embeds such values in browser code.

## Verification

```bash
npm run lint
npm test
npm run build
npm run format:check
```

The production output is `frontend/dist/` and is not committed.

## Coding Conventions

- Strict TypeScript is mandatory.
- Tests import Vitest functions explicitly and query UI by accessible role or text.
- Environment access is centralized under `src/config`.
- HTTP transport is centralized under `src/api`.
- Route composition is centralized under `src/app`.
- Shell-only context is centralized under `src/app/providers`; it must not acquire
  market, trading or other business state.
- Components do not access PostgreSQL, Dhan or backend implementation modules.
- Business calculations remain in backend services.
- ESLint handles correctness; Prettier handles formatting.
- Design-system consumers import from `src/design-system`; token and accessibility
  conventions are documented in `docs/DESIGN_SYSTEM.md`.

## API Boundary

The `ApiClient` uses native `fetch`, requires absolute-path request targets, sends
JSON acceptance headers and defaults to same-origin credentials. It currently has
no consumer and calls no endpoint.

`/api/v1` is unchanged and remains the stable Version 1 GET-only contract. V2.0.2
introduces no `/api/v2`. Later product milestones may add only the read projections
they require while keeping transport, query and business-policy boundaries distinct.

## Application Shell

V2.0.4 replaces the single foundation placeholder with a nested layout route. The
layout owns the application header, responsive primary navigation, main outlet and
status footer. Child routes remain data-free placeholders. Theme, shell state,
render-error and loading boundaries wrap the router without creating global business
state. Modal, drawer and toast hosts are UI infrastructure only.

See `docs/APPLICATION_SHELL.md` for the route map, provider order, responsive rules
and accessibility contract.

V2.0.5 replaces the Market Overview and Scanner placeholders with local-state,
native-fetch workflows and adds `/opportunities/:rankingId`. No query library or
global business state is required. See `docs/MARKET_WORKSPACE.md`.
