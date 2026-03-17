# Frontend Design

## Purpose

This document defines how the `/frontend` application should be designed going forward.

It is not a visual mood board. It is the implementation-facing design contract for:

- page structure
- visual language
- navigation
- component behavior
- API integration
- maintenance boundaries

## Current Context

- Tech base: Vite + plain ES modules
- Mount entry: `frontend/src/init.js`
- Main shell: dynamic DOM rendering into `#app`
- Backend API root: `/api/*`
- Legacy Flask template pages still exist, but they are deprecated

## Maintenance Boundary

- New frontend work must happen inside `/frontend`
- Do not extend `templates/`
- Do not extend `app/function/template/`
- Legacy template pages are compatibility-only and already marked as stopped maintenance

## Product Direction

The frontend should feel like an internal operations tool with clear hierarchy, fast scanning, and low ambiguity.

It should not look like:

- a generic admin template
- a soft pastel toy UI
- an overloaded dashboard with cards everywhere
- a mobile-first social app

It should feel like:

- structured
- calm
- operational
- slightly ceremonial to match the FAHUI domain

## Visual Direction

### Tone

Use a restrained ritual-office visual language:

- warm paper backgrounds
- dark ink text
- muted brass / wood accents
- sparse red only for warnings, deletion, or payment risk

Avoid:

- purple-heavy palettes
- neon gradients
- glassmorphism
- excessive shadows
- random rounded-card design systems

### Color System

Use CSS variables and keep color usage consistent.

Recommended base palette:

```css
:root {
  --bg-page: #f3eee3;
  --bg-panel: #fbf8f2;
  --bg-elevated: #fffdf8;
  --text-primary: #2d2418;
  --text-secondary: #6f624e;
  --line-soft: #ddd2bf;
  --line-strong: #bca98a;
  --accent: #8a6a2f;
  --accent-strong: #6f531f;
  --success: #2d6a4f;
  --warning: #b26b00;
  --danger: #a13f2f;
  --info: #315c85;
}
```

### Typography

Prefer Chinese-friendly serif/sans pairing with intention.

Recommended direction:

- headings: `"Noto Serif SC"`, `"Songti SC"`, serif
- UI/body: `"Noto Sans SC"`, `"PingFang SC"`, sans-serif
- numeric data: `"IBM Plex Sans"`, `"Noto Sans SC"`, sans-serif

Rules:

- use serif for section titles, ceremonial labels, and print-preview headers
- use sans for tables, forms, controls, and operational content
- do not use mixed novelty fonts

### Spacing

Use a predictable spacing scale:

- `4px`
- `8px`
- `12px`
- `16px`
- `24px`
- `32px`
- `48px`

Do not invent arbitrary spacing values when scale values already work.

## Layout Rules

## App Shell

The app should have a stable shell:

- top navigation on desktop
- bottom or compact horizontal nav on mobile
- one main content region
- optional right-side context panel only when needed

The shell should not reflow dramatically between pages.

## Desktop Layout

Recommended structure:

1. top app bar
2. page title row
3. action/filter row
4. content area

For data-heavy pages:

- use split layouts when detail context matters
- left: searchable list/table
- right: detail panel or quick actions

## Mobile Layout

On mobile:

- stack sections vertically
- keep primary actions sticky when necessary
- avoid complex 3-column layouts
- reduce visual decoration before reducing readability

Tables on mobile should degrade into grouped blocks instead of forcing horizontal chaos.

## Navigation

Primary sections should remain:

- Home
- Fahui Data
- Accounting
- Profile
- User Control
- Barcode

Rules:

- icons may support labels, not replace them
- active state must be obvious
- page changes should preserve context when possible
- query params can still be used, but route handling must be centralized

## Page Design Standards

## Home

The home page should act as an operational landing page, not a decorative welcome page.

Include:

- current system status
- top-level actions
- pending operational items
- recent activity or shortcuts

## Fahui Data

This is a core work page.

It should prioritize:

- search speed
- readable result density
- quick access to order details
- safe edit/delete actions

Use:

- filter bar at top
- result list or table in center
- detail drawer or detail pane

## Order Detail / Input

These pages should focus on structured editing.

Rules:

- group fields by meaning, not backend field order
- show payment state clearly
- distinguish read-only and editable fields visually
- show dangerous actions separately from normal edits

## Accounting / Payment

This area is evidence-heavy and status-heavy.

Prioritize:

- payment status color coding
- proof preview
- approval history visibility
- printable output entry points

## Barcode / Print

This area should feel tool-like:

- direct actions
- minimal decoration
- larger target sizes
- clear state after scan / generate / print

## Component Standards

## Buttons

Use clear hierarchy:

- primary: create, save, confirm, generate
- secondary: navigate, preview, filter, refresh
- danger: delete, reject, destructive operations

Do not use more than one primary action in the same action group unless required.

## Forms

Rules:

- label above field or aligned consistently
- required state explicit
- inline helper text where ambiguity exists
- validation messages close to the field
- preserve entered values on partial failure

## Tables

Tables should be used only when scanning multiple records is the main goal.

Rules:

- sticky header when content is long
- numeric columns right-aligned
- dates and status visually normalized
- row actions grouped consistently

## Status Tags

Every status must have both:

- color
- text label

Never rely on color alone.

Suggested mapping:

- approve: green
- reject: red
- pending / panding: amber
- not-ready: neutral gray-brown

## Dialogs and Drawers

Use dialogs for:

- destructive confirmation
- login
- short single-purpose actions

Use drawers or side panels for:

- order detail preview
- board placement context
- payment proof preview

## Motion

Motion should be functional, not decorative.

Allowed:

- panel slide-in
- fade for loading completion
- list/detail transition
- subtle hover emphasis

Avoid:

- bouncing
- dramatic scaling
- slow fade chains

## Data and API Rules

## Request Layer

Create a thin API layer under `frontend/src/tools/` or a dedicated `frontend/src/api/` directory.

Do not scatter `fetch()` logic arbitrarily across page files.

Recommended pattern:

- one module per backend feature
- small request helpers
- normalized JSON parsing
- shared error handling

## Error Handling

All API calls should have explicit states:

- idle
- loading
- success
- empty
- error

Every page must define what empty state and error state look like.

## Data Shaping

Frontend code should normalize backend responses near the request layer.

Do not force every UI module to repeatedly understand backend inconsistencies.

Examples to normalize:

- payment status values
- masked vs unmasked phone data
- optional nested data
- legacy success/error payload shapes

## File Organization

Recommended frontend structure:

```text
frontend/src/
  api/
  core/
  styles/
  tools/
  home/
  fahui/
  account/
  barcode/
  profile/
  user_control/
```

Within each feature:

- `init_*.js` or `page.js`: page entry
- `components/`: reusable feature-specific DOM builders
- `state.js`: feature-local state if needed
- `styles.css`: only if the feature requires isolated styling

## Styling Strategy

Move away from large inline style blocks in page initializers.

Preferred direction:

1. global design tokens in shared CSS
2. layout utility classes for shell spacing
3. feature-level CSS modules or scoped CSS files
4. minimal runtime style mutation

Inline style is acceptable only when:

- value is dynamic per record
- layout is computed from runtime data
- one-off generated print-related DOM needs it

## Accessibility

Minimum requirements:

- visible focus state
- keyboard-reachable actions
- buttons must be actual buttons where possible
- icon-only actions need labels or tooltips
- sufficient color contrast

## Design Priorities by Order

When tradeoffs happen, prioritize in this order:

1. clarity
2. data readability
3. operational speed
4. consistency
5. visual refinement

## Explicit Non-Goals

Do not optimize this frontend toward:

- trendy dashboard aesthetics
- abstract branding-first landing pages
- animation-heavy experiences
- one-component-fits-all design systems

## Definition of Done for New Frontend Work

A page or redesign is only complete when:

1. desktop and mobile layouts are both usable
2. loading, empty, and error states are present
3. API calls are centralized or reusable
4. styles follow shared tokens
5. destructive actions have confirmation
6. the page does not depend on deprecated Flask templates
