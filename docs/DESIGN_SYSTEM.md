# Version 2 Design System

## Principles

- Evidence and state must remain legible in dense trading-intelligence views.
- Semantic tokens describe purpose, not a specific color value.
- Native HTML semantics are preferred; ARIA supplements rather than replaces them.
- Keyboard operation and visible focus are required for every interactive control.
- Loading, empty, error, disabled and stale states must never rely on color alone.
- Components provide presentation and interaction primitives, not business policy.
- Responsive behavior preserves information access rather than hiding core data.

## Source Layout

```text
frontend/src/design-system/
├── tokens.css            Semantic theme and scale tokens
├── global.css            Reset, typography, focus and layout helpers
├── components.css        Component presentation
├── components.tsx        Reusable accessible React primitives
├── components.test.tsx   Behavior and accessibility tests
└── index.ts              Public design-system exports
```

The application imports the three CSS layers through `src/styles.css`. Consumers
import React primitives from `src/design-system` rather than internal files.

## Color System

The palette uses semantic roles:

- Canvas, surface, muted surface and raised surface.
- Primary, muted and inverse text.
- Default and strong borders.
- Accent and accent-hover actions.
- Success, warning, danger and information tones with paired soft backgrounds.
- Focus, overlay and scrollbar colors.

Status components pair color with text and, for status pills, a visible marker.
Text/background pairs are selected for readable contrast on the current light
theme. Product milestones must not introduce raw status colors in components.

## Typography

- `--font-sans` is the default UI family.
- `--font-serif` is reserved for prominent product headings.
- `--font-mono` is available for identifiers and technical evidence.
- The scale runs from `--text-xs` through a fluid `--text-3xl`.
- Tight and normal line-height tokens support headings and body text.
- Regular, medium, semibold and bold weight tokens establish hierarchy.

The stack uses system fonts and adds no font download or runtime dependency.

## Spacing, Shape and Elevation

Spacing follows a quarter-rem base scale from `--space-1` through `--space-16`.
Components use small, medium, large and fully rounded radius tokens. Three shadow
levels distinguish bordered cards, raised content and modal overlays.

Breakpoints are documented at 36, 48, 64 and 80 rem. CSS custom properties cannot
be used directly in media-query conditions, so styles use the matching rem values.

Z-index roles are base, sticky, dropdown, drawer, modal and toast. New components
must reuse these roles rather than invent arbitrary values.

Motion uses fast, normal and slow duration tokens plus one standard easing curve.
Global reduced-motion rules collapse decorative animation and transition duration.

## Components

Available primitives:

- `Button`: primary, secondary, quiet and danger variants; sizes; loading state.
- `Card`, `Panel`, `Divider`: content grouping and separation.
- `Badge`, `Tag`, `StatusPill`: neutral and semantic status labeling.
- `Input`, `Select`, `Checkbox`, `Toggle`: labeled native form controls.
- `Spinner`, `Skeleton`: announced and visual loading feedback.
- `EmptyState`, `ErrorState`: consistent non-data and failure presentation.
- `PageHeader`, `SectionHeader`, `Toolbar`: layout composition.
- `Modal`, `Drawer`: focus-on-open, labeled dialog and Escape-close foundations.
- `TableShell`: sticky headers, responsive overflow, loading/empty states and
  sortable-header request UI without internal sorting policy.

Example:

```tsx
import { Button, Card, StatusPill } from '../design-system'

<Card>
  <StatusPill tone="success">Ready</StatusPill>
  <Button variant="secondary">Inspect</Button>
</Card>
```

Product code owns data, sorting, state transitions and event policy. Design-system
components emit requests or callbacks but never calculate market behavior.

## Tables

`TableShell` accepts typed columns, rows and a stable row-key function. A sortable
column renders a keyboard-operable header button and emits its column key through
`onSortRequest`; it does not sort or track direction. The table uses a real caption,
scoped headers and a named scroll region. Numeric alignment uses tabular figures.

Wide tables remain horizontally scrollable rather than hiding columns. Loading and
empty inputs render their corresponding reusable states instead of malformed table
rows.

## Forms

Inputs and selects use explicit labels and separate hint/error descriptions.
Validation sets `aria-invalid` and connects the description with
`aria-describedby`. Checkboxes remain native inputs. Toggle is a native button with
`role="switch"` and `aria-checked`.

No business form, schema validator or form-state library is included in V2.0.3.

## Accessibility Rules

- Interactive elements must be reachable and operable by keyboard.
- Global `:focus-visible` rings must not be removed without an accessible replacement.
- Icon-only buttons require an accessible label.
- Decorative icons use `aria-hidden="true"`.
- Dialogs require an accessible title, modal semantics and Escape handling.
- Loading indicators expose a status label; decorative animation is hidden.
- Empty and error messages use headings and readable descriptions.
- Disabled controls use native `disabled` where available.
- Tests query controls by role, name and accessible description.

The modal and drawer are foundations. More advanced focus containment and focus
restoration should be completed when V2.0.4 establishes application-level overlay
composition.

## Responsive Philosophy

- The minimum supported viewport is 320 pixels.
- Containers use narrow mobile gutters and wider desktop gutters.
- Headers and toolbars wrap instead of truncating actions.
- Data tables use named horizontal scroll regions.
- Drawers occupy the viewport edge; modals retain safe viewport margins.
- Components avoid product-specific fixed widths.

## Icons

`lucide-react` is the only icon library. It supplies consistent SVG React
components, is tree-shakeable and does not require an icon font or global asset.
Only imported icons enter a production bundle. Icons supplement text; they do not
replace accessible names.

## Future Dark Mode

All component CSS references semantic tokens. A complete dark token set is defined
under `[data-theme='dark']`, but no switch, persistence or automatic theme selection
is implemented. V2.0.16 owns theme preferences. Until then, the application uses
the light theme and the dark values serve as an architectural compatibility check.
