# Retro 005 — board-ui

**Feature:** [feature-005-board-ui](../requirements/feature-005-board-ui.md) (issue #2)

## What we did

Render-only `Board` / `Section` / `Card` components under `app/src/components/`, wired into
`App.tsx` as `<Board cards={mockCards} />` beneath the feature-001 greeting `<h1>`. `Board`
delegates all grouping/sorting/merging to the existing pure `groupByCategory` (feature 003)
and renders the "paste a link to start" empty state when it returns nothing. Card titles
link to the article (`target="_blank" rel="noopener noreferrer"`); summary, key points,
tag chips, and a category badge complete each card. Minimal inline styles only (max-width
container, bordered/rounded card boxes, chip pills), per constraints. 21/21 tests, lint,
and build all green — no new tests because no new logic exists.

## What worked

- The pure-module discipline paid off exactly as designed: the components needed zero new
  logic and therefore zero new specs. The only "computation" in any component is reading
  `sections.length` off `groupByCategory`'s output to pick the empty state.
- The feature-003 mock fixtures made the UI verifiable at a glance — the
  "AI"/"Artificial Intelligence" near-duplicate pair visibly merges into one section the
  first time the board renders, demoing feature 002 in the browser with no extra work.
- Reusing the bootstrap CSS variables (`--border`, `--accent`, `--code-bg`) inside inline
  styles, with hex fallbacks, kept the board legible in both light and dark schemes without
  adding any stylesheet or framework.

## Friction

- The component named `Card` collides with the `Card` type from `app/src/types.ts`;
  resolved with `import type { Card as CardModel }`. Cosmetic, but every future component
  rendering a model with the same name will repeat this dance — a `*Model` alias convention
  is worth keeping consistent.
- The bootstrap `index.css` sets `#root { text-align: center }`, so the board components
  each carry `textAlign: 'left'` inline. Fine at this scale; when a styling ADR lands, the
  centering should move out of the global `#root` rule.

## Changes

- None to the working agreement; rule 5 (no DOM tests without an ADR) held comfortably for
  a pure-render slice. Suggested "Current state" addition for the orchestrator: board UI
  (feature 005 / issue #2) renders `mockCards` in merged topic sections with an empty
  state; PLAN build step 1 now only needs `UrlInput` (#3) and `lib/api.ts` (#4).
